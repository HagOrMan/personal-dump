# About
This is the entry point for all of my personal notes. What does it tell you? That remains to be seen.

If you're curious why I started this in the first place, check out [my file on why I made a digital vault](notes/WhyADigitalVault.md).

# A Secret
I never directly commit to this repo :exploding_head:

**Let's look at some history:**  
This repo was once meant for a dump of personal items that I wanted the world, or myself when not signed into GitHub, to have access to. For a while, I would just gitignore the files that should remain private, such a works in progress that I wasn't ready to share. So technically I did commit to it at some point.

~~And then the fire nation attacked~~ And then I had the wonderful idea to maintain two repositories. Why? Because it gives me 3 stages of files:
1. Public
2. Private
3. Local

While I could do this in separate repos, I had the brilliant (or perhaps just overcomplicating) idea to put it in a singular repo. I wanted these files to be accessible as part of the same file system, partially for my own sense of organization within a file system and partially because I wanted to use Obsidian for the repo, and have it set up at the repo root rather than as the parent folder to two repos.

## How did I do it?
For anyone curious enough to read this far, the secret lies in GitHub Actions and Personal Access Tokens. Here are the steps:
1. I decided my workflow would consist of using a suffix, `_public`, on files which I wanted pushed to the public version of the repo.
2. I made a private version of this repo and copied all my files over.
3. I made a fine-grained Personal Access Token (PAT) with access to this public repo and gave it `Read/Write` permissions on `Content`. ([instructions for making a fine-grained PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token))
4. I added the token as a secret to the private version of this repo, naming the token `PUBLIC_REPO_PAT`.
5. I made a GitHub actions workflow with [a lot of testing](#trials-and-tribulations-in-my-endeavor) and ensured it not only stripped `_public` from the file name of files I wanted pushed to the public repo, but accordingly adjusted the markdown references to these files.

Here is the workflow I used (which I thought I would have to redact but there is no private info in it):
```yml
name: Publish Public Files

on:
  push:
    branches:
      - main

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout private repo
        uses: actions/checkout@v3

      - name: Set up Git
        run: |
          git config --global user.name "Kyle"
          git config --global user.email "86536365+HagOrMan@users.noreply.github.com"

      - name: Clone public repo
        env:
          REPO_URL: https://x-access-token:${{ secrets.PUBLIC_REPO_PAT }}@github.com/HagOrMan/personal-dump.git
        run: |
          git clone $REPO_URL public_repo
          cd public_repo
          git checkout main || git checkout -b main
          cd ..

      - name: Get changed _public.md files
        id: changed_public
        run: |
          CHANGED_PUBLIC_FILES=$(git diff --name-only origin/main...HEAD | grep '_public\.md$' || true)
          echo "CHANGED_PUBLIC_FILES<<EOF" >> $GITHUB_ENV
          echo "$CHANGED_PUBLIC_FILES" >> $GITHUB_ENV
          echo "EOF" >> $GITHUB_ENV

      - name: Sync public files (add, update, delete)
        run: |
          # Clean everything except the .git folder so deletions are detected
          find public_repo -mindepth 1 -not -path "public_repo/.git*" -exec rm -rf {} +

          # Copy public files preserving structure
          find . -type f -name '*_public.*' | while read file; do
            # Remove the leading ./ from file path
            relative_path="${file#./}"
            
            # Compute destination directory inside public_repo
            dest_dir="public_repo/$(dirname "$relative_path")"
            mkdir -p "$dest_dir"
            
            new_name=$(basename "$relative_path" | sed 's/_public\././')   # remove _public before the extension
            cp "$file" "$dest_dir/$new_name"
          done

      - name: Fix markdown references only in changed files
        if: env.CHANGED_PUBLIC_FILES != ''
        run: |
          echo "$CHANGED_PUBLIC_FILES" | while read file; do
            # Skip empty lines
            [ -z "$file" ] && continue

            # Remove leading ./ if present
            file="${file#./}"

            # Convert e.g. docs/guide_public.md → docs/guide.md
            public_path="${file/_public/}"

            # Full path in public repo
            public_file="public_repo/$public_path"

            if [ -f "$public_file" ]; then
              echo "Fixing markdown references in: $public_file"

              # Inline links/images
              sed -i -E 's@(\]\([^)]*?)_public(\.[^)/?#]+)([?#][^)]*)?@\1\2\3@g' "$public_file"
              # Reference-style links
              sed -i -E 's@(\[[^]]*\]:[[:space:]]*)([^:)]*)_public(\.[^)/?#]+)([?#][^)]*)?@\1\2\3\4@g' "$public_file"
            else
              echo "Skipping $public_file (not found)"
            fi
          done

      - name: Commit and push changes to public repo
        working-directory: public_repo
        run: |
          git add -A
          git commit -m "${{ github.event.head_commit.message }}" || echo "No changes to commit"
          git push origin main
```

## Trials and Tribulations in my Endeavor
1. To test whether the first version of pushing `_public` files worked, I made two test repos. This was just a lot of effort and setup, but worth it for the peace of mind that my precious `personal-dump` repo would not be destroyed when I started pushing to it from my private version.
2. In doing so, it became more complicated than I thought because I needed to detect files that were deleted and ensure they got deleted in the public version of the repo.
3. I realized that markdown links to other files would be destroyed if I was stripping `_public` from the file names, so I needed to accordingly change all markdown reference links, whether inline, images, or reference links at the bottom of the page.
	- This had to be optimized on its own to specifically look through markdown files which changed in the latest commit to my private repo and ended in `_public.md`.
	- This required going through all markdown files which changed and stripping `_public` ONLY from references to other files within the repo.
	- I ran into issues such as it accidentally stripping `_public` from a URL.
4. I then tested everything in a minimal test repo, ensuring the substitutions worked well.
5. After that, I ran the workflow in my private repo but without the step that commits to the public repo, as one final check that the modifications to the public repo looked the way I wanted them to.
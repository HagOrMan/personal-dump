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
6. I then wanted my commits to show up as verified when pushing to the public repo, so I added a GPG key named `GPG_PRIVATE_KEY` and a step in the workflow to use it for verification when committing code. ([instructions for generating a GPG key](https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key#generating-a-gpg-key), and [instructions for adding it to your profile](https://docs.github.com/en/authentication/managing-commit-signature-verification/adding-a-gpg-key-to-your-github-account#adding-a-gpg-key))
7. I added a summary to the pipeline, which displays in markdown when I click on the workflow run to give a clean note on how the run went and what occured. This was simply by adding `>> $GITHUB_STEP_SUMMARY` after any echo statement, and formatting them with markdown headings, codeblocks, and lists.

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
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Import GPG key
        run: |
          mkdir -p ~/.gnupg
          echo "$GPG_PRIVATE_KEY" | gpg --batch --import
          echo "use-agent" >> ~/.gnupg/gpg.conf
          echo "pinentry-mode loopback" >> ~/.gnupg/gpg.conf
          git config --global user.signingkey "$(gpg --list-secret-keys --keyid-format=long | grep sec | head -n1 | awk '{print $2}' | cut -d'/' -f2)"
          git config --global commit.gpgSign true
        env:
          GPG_PRIVATE_KEY: ${{ secrets.GPG_PRIVATE_KEY }}

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
          echo "# Check changed public files" >> $GITHUB_STEP_SUMMARY
          CHANGED_PUBLIC_MARKDOWN_FILES=$(git diff --name-only ${{ github.event.before }} ${{ github.sha }} -- '*_public.md')
          echo "CHANGED_PUBLIC_MARKDOWN_FILES<<EOF" >> $GITHUB_ENV
          echo "$CHANGED_PUBLIC_MARKDOWN_FILES" >> $GITHUB_ENV
          echo "EOF" >> $GITHUB_ENV

          CHANGED_PUBLIC_FILES=$(git diff --name-status ${{ github.event.before }} ${{ github.sha }} -- '*_public.*')
          echo "CHANGED_PUBLIC_FILES<<EOF" >> $GITHUB_ENV
          echo "$CHANGED_PUBLIC_FILES" >> $GITHUB_ENV
          echo "EOF" >> $GITHUB_ENV

          # Log the changed files to the summary as well
          echo "## Changed public markdown" >> $GITHUB_STEP_SUMMARY
          echo "$CHANGED_PUBLIC_MARKDOWN_FILES" >> $GITHUB_STEP_SUMMARY
          echo "## Changed public (all file extensions)" >> $GITHUB_STEP_SUMMARY
          echo "$CHANGED_PUBLIC_FILES" >> $GITHUB_STEP_SUMMARY

      - name: Sync public files (add, update, delete)
        if: env.CHANGED_PUBLIC_FILES != ''
        run: |
          echo "# Syncing public files" >> $GITHUB_STEP_SUMMARY

          # Copy public files preserving structure
          echo "$CHANGED_PUBLIC_FILES" | while read status src dest; do
            case "$status" in
              # This is for additions or modifications
              A|M)
                # Remove the leading ./ from file path
                # src is the path of the _public file
                relative_path="${src#./}"

                # Compute destination directory inside public_repo
                dir_new="$(dirname "$relative_path")"
                if [ "$dir_new" = "." ]; then
                  dest_dir="public_repo"
                else
                  dest_dir="public_repo/$dir_new"
                fi
                mkdir -p "$dest_dir"

                new_name=$(basename "$relative_path" | sed 's/_public\././') # remove _public before the extension
                cp "$src" "$dest_dir/$new_name"
                echo "- added/modified file \`$dest_dir/$new_name\`" >> $GITHUB_STEP_SUMMARY
                ;;

              # This is for deletions
              D)
                # Remove the leading ./ from file path
                # src is the previous _public file path
                relative_path="${src#./}"

                # Compute destination directory inside public_repo
                dir_old="$(dirname "$relative_path")"
                if [ "$dir_old" = "." ]; then
                  dest_dir="public_repo"
                else
                  dest_dir="public_repo/$dir_old"
                fi
                old_name=$(basename "$relative_path" | sed 's/_public\././') # remove _public before the extension

                # Delete if it exists
                if [ -f "$dest_dir/$old_name" ]; then
                  rm "$dest_dir/$old_name"
                  echo "- deleted from \`$dest_dir/$old_name\`" >> $GITHUB_STEP_SUMMARY
                else
                  echo "- ⚠️ could not delete \`$dest_dir/$old_name\` (not found)" >> $GITHUB_STEP_SUMMARY
                fi
                
                ;;

              # This is for renames
              R*)
                # Remove the leading ./ from file path
                # For renames, both src (old) and dest (new) are provided
                old_relative="${src#./}"
                new_relative="${dest#./}"

                # Compute destination directory inside public_repo
                dir_old="$(dirname "$old_relative")"
                if [ "$dir_old" = "." ]; then
                  old_dir="public_repo"
                else
                  old_dir="public_repo/$dir_old"
                fi

                dir_new="$(dirname "$new_relative")"
                if [ "$dir_new" = "." ]; then
                  new_dir="public_repo"
                else
                  new_dir="public_repo/$dir_new"
                fi

                # remove _public before the extension
                old_name=$(basename "$old_relative" | sed 's/_public\././')
                new_name=$(basename "$new_relative" | sed 's/_public\././')

                # Ensure destination exists
                mkdir -p "$new_dir"

                # If old file exists, rename it; otherwise just copy the new one
                if [ -f "$old_dir/$old_name" ]; then
                  mv "$old_dir/$old_name" "$new_dir/$new_name"
                  echo "- renamed \`$old_dir/$old_name\` to \`$new_dir/$new_name\`" >> $GITHUB_STEP_SUMMARY
                else
                  cp "$dest" "$new_dir/$new_name"
                  echo "- copied \`$dest\` to \`$new_dir/$new_name\`, could not find the old file" >> $GITHUB_STEP_SUMMARY
                fi
                ;;
            esac
          done

      - name: Fix markdown references only in changed files
        if: env.CHANGED_PUBLIC_MARKDOWN_FILES != ''
        run: |
          echo >> $GITHUB_STEP_SUMMARY
          echo "# Beginning to fix markdown references in files" >> $GITHUB_STEP_SUMMARY
          echo "$CHANGED_PUBLIC_MARKDOWN_FILES" | while read file; do
            # Skip empty lines
            [ -z "$file" ] && continue

            # Remove leading ./ if present
            file="${file#./}"

            # Convert e.g. docs/guide_public.md → docs/guide.md
            public_path="${file%_public.*}.${file##*.}"

            # Full path in public repo
            public_file="public_repo/$public_path"

            if [ -f "$public_file" ]; then
              echo "- \`$public_file\`" >> $GITHUB_STEP_SUMMARY

              # Inline links/images
              sed -i -E 's@(\]\([^)]*?)_public(\.[^)/?#]+)([?#][^)]*)?@\1\2\3@g' "$public_file"
              # Reference-style links
              sed -i -E 's@(\[[^]]*\]:[[:space:]]*)([^:)]*)_public(\.[^)/?#]+)([?#][^)]*)?@\1\2\3\4@g' "$public_file"
            else
              echo "- ⚠️ Skipping \`$public_file\` (not found)" >> $GITHUB_STEP_SUMMARY
            fi
          done

      - name: Commit and push changes to public repo
        working-directory: public_repo
        run: |
          git add -A

          echo "# Check repo before commit" >> $GITHUB_STEP_SUMMARY
          echo '🔍 Final repo status:' >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          git status >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY

          echo >> $GITHUB_STEP_SUMMARY
          echo '🔍 Pending changes:' >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          git diff --cached >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY

          git commit -S -m "${{ github.event.head_commit.message }}" || { echo "**No changes to commit**" >> $GITHUB_STEP_SUMMARY; }
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
6. I realized that my code didn't actually work, because the changed files weren't being fetched from git correctly. This required changing how the private repo is checked out in the first stage of the `.yml` file, and modifying the `git diff` line to use `github.event.before`.
7. I then realized with some more testing that subfolders didn't work, as the `_public` would be stripped from folder names as well if they existed. This required a small regex change.
8. I found that files which were markdown but not modified in the latest commit would have their processing undone, so I had to make a "smarter" version of the script which only touched modified files.
   - This was fun because I also explored GitHub Actions Summary in doing so for testing, and the output of the automated workflows has never looked nicer.
   - It took effort and testing to make sure the file paths looked good, the correct files were modified, and then that the logging worked properly.
   - I tested every case of addition, modification, deletion, and rename, and dealt with a file path with an extra `./`, plus my logs not displaying anything because I didn't escape the \` which surrounded the file name (I logged something like "added file `file.txt`").
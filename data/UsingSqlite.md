When opening sqlite in git bash, it may not work for some reason. If this happens, run
```bash
winpty sqlite3
```
and it should open.

To open a database that already exists (or that you want to create), run 
```bash
winpty sqlite3 your_file.db
```

To view all tables
```bash
.tables
```

To see all items in one table
```bash
Select * from TABLE
```

It's basically the same as regular sql once you're this far in

To close the sqlite3 terminal
```bash
.exit
```

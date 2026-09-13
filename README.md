# Your portfolio site, fresh setup guide

This is a clean start with a simpler structure. Only two files sit at the top level of your repository, nothing nested in folders, so there is nothing to mismatch this time.

## 1. Delete your current repository

Go to your existing repository (mohsinrasheed1.github.io), click Settings, scroll all the way to the bottom to the Danger Zone, and choose Delete this repository. GitHub will ask you to type the repository name to confirm.

## 2. Create a new repository with the same name

Click the plus icon in the top right, then New repository. Name it exactly:

```
mohsinrasheed1.github.io
```

Set it to Public. Do not add a README from GitHub's side.

## 3. Upload exactly two files

On the new repository's page, click Add file, then Upload files, and drag in:

- index.html
- your CV, renamed exactly to cv.pdf (all lowercase)

Commit the upload.

## 4. Turn on GitHub Pages

Go to Settings, then Pages in the left sidebar. Under Build and deployment, set Source to Deploy from a branch, Branch to main, folder to / (root), then Save.

## 5. Check your site

Wait a minute or two, then visit:

```
https://mohsinrasheed1.github.io
```

Click Download CV to confirm it opens your actual CV, since the button is already pointing to the exact filename cv.pdf sitting at the top level.

## Adding a project later

When your first case study is ready, come back and I will write the new section and add it directly into index.html.

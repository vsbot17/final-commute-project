# GitHub Pages Setup Instructions

## Important: Configure GitHub Pages Correctly

Your site is built and ready in the `docs/` folder. To make it work on GitHub Pages:

### Option 1: Use GitHub Actions (Recommended)

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under **Source**, select **"GitHub Actions"**
4. The workflow will automatically deploy on every push to main

### Option 2: Use /docs folder manually

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under **Source**, select **"Deploy from a branch"**
4. Select your branch (usually `main` or `master`)
5. Select the folder: **`/docs`** (NOT root!)
6. Click **Save**

## After Configuration

Your site will be available at:
- `https://vsbot17.github.io/FinalViz/`

## Troubleshooting

If you still see README.md:
- Make sure the Source is set to `/docs` folder, NOT root
- Wait a few minutes for GitHub Pages to update
- Clear your browser cache
- Check that `docs/index.html` exists in your repository

## Files That Should Be in `docs/` Folder

After building with `npm run build`, you should have:
- `docs/index.html` ✓
- `docs/_app/` folder ✓
- `docs/.nojekyll` ✓
- `docs/*.json` (data files) ✓


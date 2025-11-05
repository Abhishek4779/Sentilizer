# ML Models Directory

This folder must contain the trained sentiment analysis models for the app to work.

## Required Files:
1. **log_reg.pkl** - Logistic Regression sentiment model
2. **tfidf.pkl** - TF-IDF vectorizer for text processing

## Important:
⚠️ These files are required for the app to start. Without them, the app will crash with:
```
FileNotFoundError: Model or vectorizer file not found
```

## How to add the models:
1. Get the `.pkl` files from your local development environment
2. Place them in this `models/` directory
3. Commit and push to deploy

**Note:** If model files are very large (>100MB), consider using Git LFS or cloud storage.


# StayScout - Quick Start Guide

Deploy your production-ready demo to Vercel in 10 minutes.

## What You're Deploying

A beautiful, professional demo website for StayScout that showcases:
- AI-powered vacation rental price comparison
- Real demo data showing $500+ savings
- Interactive price comparison tables
- Mobile-responsive design
- Professional branding
- Ready for affiliate program applications

**Live Site:** https://stayscoutapp.com (after deployment)

## Prerequisites (5 minutes)

1. **GitHub Account** - Sign up at https://github.com
2. **Vercel Account** - Sign up at https://vercel.com (use GitHub login)
3. **Domain Access** - Access to stayscoutapp.com DNS settings

## Deployment Steps

### Step 1: Push to GitHub (3 minutes)

```bash
# Navigate to project
cd /mnt/c/Users/georg/OneDrive/Documents/git/bnbsaver/bnbsaver

# Initialize git (if not already done)
git init

# Add all deployment files
git add application.py demo_results.py vercel.json requirements-demo.txt .vercelignore
git add templates/ static/ README_DEPLOY.md

# Commit
git commit -m "StayScout production demo - ready for Vercel"

# Create GitHub repo and push
# (Create repo at github.com/new first, name it "stayscout-demo")
git remote add origin https://github.com/YOUR_USERNAME/stayscout-demo.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Vercel (2 minutes)

1. Go to https://vercel.com
2. Click **"Add New..." → "Project"**
3. Import your `stayscout-demo` repository
4. Configure:
   - **Install Command:** `pip install -r requirements-demo.txt`
   - Leave everything else as default
5. Add Environment Variables:
   - `FLASK_ENV` = `production`
   - `SECRET_KEY` = Generate with:
     ```bash
     python3 -c "import secrets; print(secrets.token_hex(32))"
     ```
6. Click **"Deploy"**
7. Wait 1-2 minutes

**You now have a live site!** (e.g., https://stayscout-demo.vercel.app)

### Step 3: Connect Domain (5 minutes)

**In Vercel:**
1. Go to your project → **Settings** → **Domains**
2. Add `stayscoutapp.com`
3. Add `www.stayscoutapp.com`

**In Your Domain Registrar (Namecheap, GoDaddy, etc.):**
1. Log in to your domain registrar
2. Go to DNS settings
3. Add these records:

```
Type: A
Name: @ (or leave blank)
Value: 76.76.21.21
TTL: 3600

Type: CNAME
Name: www
Value: cname.vercel-dns.com
TTL: 3600
```

4. Save changes
5. Wait 10-30 minutes for DNS propagation
6. Return to Vercel and click "Refresh" next to your domain

**Done!** Your site is live at https://stayscoutapp.com

## Verify Deployment

Visit your site and check:
- ✅ Home page loads with demo
- ✅ Demo page shows price comparison
- ✅ About page works
- ✅ Navigation functions
- ✅ Mobile responsive
- ✅ HTTPS enabled (green padlock)

## What's Included

### Pages
- **Home (`/`)** - Landing page with hero, how it works, live demo preview
- **Demo (`/demo`)** - Interactive demo with full price comparison
- **About (`/about`)** - Mission, technology, team info

### Features
- Professional StayScout branding
- Bootstrap 5 responsive design
- Custom color scheme (blues/greens)
- Real demo data from Park City & Miami Beach
- Email signup forms (currently show alerts)
- SEO-optimized meta tags
- Custom 404/500 error pages
- Fast loading (minimal dependencies)

### Tech Stack
- **Backend:** Flask 3.0
- **Frontend:** Bootstrap 5, Custom CSS
- **Hosting:** Vercel (serverless)
- **Domain:** stayscoutapp.com

## File Structure

```
bnbsaver/
├── application.py          # Main Flask app (production)
├── demo_results.py         # Demo data
├── vercel.json            # Vercel config
├── requirements-demo.txt  # Minimal dependencies
├── .vercelignore         # Deployment exclusions
├── templates/            # HTML templates
│   ├── base.html        # Base layout
│   ├── home.html        # Landing page
│   ├── demo.html        # Interactive demo
│   ├── about.html       # About page
│   ├── 404.html         # Not found page
│   └── 500.html         # Error page
└── static/
    └── css/
        └── style.css     # Custom StayScout styles
```

## Customization

### Update Branding
Edit `application.py`:
```python
BRAND_CONFIG = {
    'name': 'StayScout',
    'domain': 'stayscoutapp.com',
    'tagline': 'Find the Best Price for Your Perfect Stay',
    'description': 'Your description here'
}
```

### Update Colors
Edit `static/css/style.css`:
```css
:root {
    --primary: #0066CC;      /* Main blue */
    --secondary: #00CC66;    /* Success green */
    --accent: #FF6B35;       /* Action orange */
}
```

### Update Demo Data
Edit `demo_results.py` to change the example properties shown.

## Making Updates

Any push to `main` branch automatically deploys:

```bash
# Make changes
git add .
git commit -m "Update homepage copy"
git push origin main
```

Vercel automatically rebuilds and deploys in 1-2 minutes.

## Costs

**FREE** for demo site!

Vercel free tier includes:
- Unlimited deployments
- 100GB bandwidth/month
- Automatic HTTPS
- Custom domains

This is more than enough for a demo/portfolio site.

## Next Steps

### 1. Test Everything
- Browse all pages
- Test on mobile
- Check email forms
- Verify SEO tags

### 2. Apply to Affiliate Programs
Now that you have a live site:
- **VRBO:** https://www.vrbo.com/affiliate
- **Booking.com:** https://www.booking.com/affiliate
- **Agoda:** https://www.agoda.com/affiliate

### 3. Gather Early Access Signups
Share your site:
- Friends and family
- Social media
- Travel communities
- Reddit (r/travel, r/digitalnomad)

### 4. Monitor Performance
- Enable Vercel Analytics
- Check visitor stats
- Monitor uptime
- Gather feedback

### 5. Plan Full Product
- Real scraping integration
- User accounts
- Save searches
- Email alerts
- Premium features

## Troubleshooting

**Build fails?**
- Check `requirements-demo.txt` exists
- Verify all templates are in `templates/` folder
- Check Vercel build logs

**Domain not working?**
- Verify DNS records are correct
- Wait 24-48 hours for propagation
- Clear browser cache
- Try incognito mode

**Page not found?**
- Check `vercel.json` routing
- Verify template file names match routes
- Check for typos in URLs

**Slow loading?**
- Enable Vercel Analytics to diagnose
- Check image sizes
- Verify CDN links working

## Get Help

- **Full Deployment Guide:** See `README_DEPLOY.md`
- **Deployment Checklist:** See `DEPLOYMENT_CHECKLIST.md`
- **Vercel Docs:** https://vercel.com/docs
- **Vercel Support:** https://vercel.com/support

## Success!

You now have a professional, production-ready demo website that:
- Looks impressive for affiliate applications
- Gathers early access signups
- Demonstrates your AI price comparison concept
- Serves as a portfolio piece
- Costs $0 to run

**Share it proudly!** 🎉

---

**Need more help?** Check the detailed guides:
- `README_DEPLOY.md` - Complete deployment instructions
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist

# StayScout - Vercel Deployment Guide

Complete step-by-step instructions to deploy StayScout to Vercel and connect your custom domain.

## Prerequisites

- Git installed on your computer
- A GitHub account
- A Vercel account (free tier is sufficient)
- Domain access to stayscoutapp.com

## Step 1: Prepare Your Repository

### 1.1 Initialize Git Repository (if not already done)

```bash
cd /mnt/c/Users/georg/OneDrive/Documents/git/bnbsaver/bnbsaver
git init
```

### 1.2 Create .gitignore (if not exists)

Ensure your `.gitignore` includes:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
venv_wsl/
env/
ENV/

# Flask
instance/
.webassets-cache

# Environment variables
.env
.env.local

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Vercel
.vercel

# Development files
*.log
*.pot
*.pyc
```

### 1.3 Stage and Commit Files

```bash
# Add demo deployment files
git add application.py
git add demo_results.py
git add templates/
git add static/
git add vercel.json
git add requirements-demo.txt
git add README_DEPLOY.md
git add .vercelignore

# Commit
git commit -m "Initial StayScout demo deployment setup"
```

### 1.4 Push to GitHub

```bash
# Create a new repository on GitHub (e.g., stayscout-demo)
# Then push your code:

git remote add origin https://github.com/YOUR_USERNAME/stayscout-demo.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy to Vercel

### 2.1 Sign Up / Log In to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Sign up or log in (recommended: use GitHub login)

### 2.2 Import Your Project

1. Click **"Add New..."** → **"Project"**
2. Import your GitHub repository (`stayscout-demo`)
3. Vercel will auto-detect it as a Python project

### 2.3 Configure Project Settings

In the import screen, configure:

**Framework Preset:** Other (Vercel will use the config from vercel.json)

**Root Directory:** `./` (leave as default)

**Build Command:** Leave empty (handled by vercel.json)

**Install Command:** `pip install -r requirements-demo.txt`

**Environment Variables:**

Add these environment variables (click "Environment Variables"):

- `FLASK_ENV` = `production`
- `SECRET_KEY` = `[generate a secure random key]`

To generate a secure secret key, run in terminal:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2.4 Deploy

1. Click **"Deploy"**
2. Wait 1-2 minutes for the build to complete
3. You'll get a live URL like: `https://stayscout-demo.vercel.app`

### 2.5 Test Your Deployment

Visit your Vercel URL and verify:
- [ ] Home page loads correctly
- [ ] Demo page shows data properly
- [ ] About page is accessible
- [ ] Navigation works
- [ ] Forms submit (even if just alerts)
- [ ] Mobile responsive design works

## Step 3: Connect Custom Domain (stayscoutapp.com)

### 3.1 Add Domain in Vercel

1. In your Vercel project, go to **Settings** → **Domains**
2. Enter `stayscoutapp.com` and click **Add**
3. Also add `www.stayscoutapp.com`
4. Vercel will show DNS records you need to configure

### 3.2 Configure DNS Records

You'll need to add these records in your domain registrar (e.g., Namecheap, GoDaddy, Cloudflare):

**For Apex Domain (stayscoutapp.com):**
```
Type: A
Name: @
Value: 76.76.21.21
TTL: 3600
```

**For WWW Subdomain:**
```
Type: CNAME
Name: www
Value: cname.vercel-dns.com
TTL: 3600
```

**Instructions for common registrars:**

**Namecheap:**
1. Log in to Namecheap
2. Go to Domain List → Manage → Advanced DNS
3. Add the A record and CNAME record above
4. Save changes

**GoDaddy:**
1. Log in to GoDaddy
2. My Products → DNS → Manage Zones
3. Add records as specified
4. Save

**Cloudflare:**
1. Log in to Cloudflare
2. Select your domain
3. Go to DNS settings
4. Add the records (set Proxy status to "Proxied" for HTTPS)

### 3.3 Verify Domain

1. Back in Vercel, wait 5-10 minutes for DNS propagation
2. Click **"Refresh"** next to your domain
3. Once verified, you'll see a green checkmark
4. Vercel automatically provisions SSL certificate (HTTPS)

**Note:** DNS propagation can take up to 48 hours, but usually works within 10-30 minutes.

### 3.4 Set Primary Domain

1. In Vercel Domains settings
2. Click the three dots next to `stayscoutapp.com`
3. Select **"Set as Primary"**
4. This ensures www redirects to the main domain

## Step 4: Configure Production Settings

### 4.1 Enable Analytics (Optional)

1. Go to your project in Vercel
2. Click **Analytics** tab
3. Enable Web Analytics (free)
4. Track page views, performance, etc.

### 4.2 Set Up Speed Insights (Optional)

1. In your Vercel project
2. Click **Speed Insights** tab
3. Enable for performance monitoring

### 4.3 Environment Variables for Production

Verify in **Settings** → **Environment Variables**:

```
FLASK_ENV=production
SECRET_KEY=your-secure-random-key-here
```

## Step 5: Post-Deployment Testing

### 5.1 Full Site Test Checklist

Visit `https://stayscoutapp.com` and test:

- [ ] Home page loads with demo data
- [ ] All navigation links work
- [ ] Demo page displays price comparisons
- [ ] About page loads correctly
- [ ] Email signup forms show confirmation
- [ ] All buttons and CTAs work
- [ ] Mobile responsive (test on phone)
- [ ] Social sharing (if implemented)
- [ ] 404 page works (try /nonexistent)
- [ ] HTTPS is enabled (green padlock)

### 5.2 Performance Testing

Test site speed:
- [Google PageSpeed Insights](https://pagespeed.web.dev/)
- [GTmetrix](https://gtmetrix.com/)
- [WebPageTest](https://www.webpagetest.org/)

Target scores:
- Performance: 90+
- Accessibility: 90+
- Best Practices: 90+
- SEO: 90+

### 5.3 SEO Verification

Verify SEO setup:
- [ ] Meta descriptions are present
- [ ] Open Graph tags work
- [ ] Structured data (if added)
- [ ] Sitemap accessible
- [ ] robots.txt configured

## Step 6: Continuous Deployment

Vercel automatically deploys on every push to `main` branch.

### 6.1 Making Updates

```bash
# Make your changes
git add .
git commit -m "Description of changes"
git push origin main
```

Vercel will automatically:
1. Detect the push
2. Build your project
3. Deploy to production
4. Update stayscoutapp.com

### 6.2 Preview Deployments

Every pull request gets a unique preview URL:
1. Create a new branch
2. Make changes
3. Push and create PR
4. Vercel comments with preview URL
5. Test before merging

## Step 7: Monitoring & Maintenance

### 7.1 Monitor Deployment Status

- Check Vercel dashboard for deployment logs
- Set up Vercel notifications (Settings → Notifications)
- Monitor uptime with external service (e.g., UptimeRobot)

### 7.2 View Logs

```
Vercel Dashboard → Your Project → Deployments → View Function Logs
```

### 7.3 Rollback (if needed)

If a deployment breaks:
1. Go to Deployments tab
2. Find the last working deployment
3. Click "..." → "Promote to Production"

## Troubleshooting

### Issue: Build Fails

**Check:**
- requirements-demo.txt is correct
- All imports in application.py are available
- No syntax errors in Python files

**Solution:**
```bash
# Test locally first
pip install -r requirements-demo.txt
python application.py
```

### Issue: 404 Errors

**Check:**
- vercel.json routing configuration
- Template files are in templates/ folder
- Static files are in static/ folder

### Issue: Slow Performance

**Solutions:**
- Enable Vercel Analytics to identify bottlenecks
- Optimize images (use WebP format)
- Minimize CSS/JS
- Enable caching headers

### Issue: Domain Not Connecting

**Check:**
- DNS records are correct
- Wait 24-48 hours for full propagation
- Try clearing browser cache
- Test with `dig stayscoutapp.com` in terminal

### Issue: HTTPS Certificate Issues

**Solution:**
- Vercel auto-provisions SSL
- If issues persist, remove and re-add domain
- Contact Vercel support

## Advanced Configuration

### Custom Build Settings

Edit `vercel.json` to customize:

```json
{
  "functions": {
    "application.py": {
      "memory": 1024,
      "maxDuration": 10
    }
  }
}
```

### Environment-Specific Configs

Use different env vars for staging vs production:
- Production: Auto-deploy from `main` branch
- Staging: Auto-deploy from `develop` branch

### Custom Headers

Add to `vercel.json`:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        }
      ]
    }
  ]
}
```

## Getting Help

- **Vercel Documentation:** https://vercel.com/docs
- **Vercel Support:** https://vercel.com/support
- **Vercel Discord:** https://vercel.com/discord
- **Email:** support@stayscoutapp.com (update with your real email)

## Next Steps After Deployment

1. **Set up email marketing** (ConvertKit, Mailchimp)
2. **Add Google Analytics** for tracking
3. **Submit to search engines** (Google Search Console, Bing Webmaster)
4. **Create social media accounts** (Twitter, Instagram)
5. **Apply for affiliate programs** with active demo site
6. **Gather user feedback** from early access list
7. **Plan feature roadmap** for full product launch

## Security Checklist

- [ ] HTTPS enabled (automatic with Vercel)
- [ ] Environment variables secured (not in code)
- [ ] No API keys in frontend code
- [ ] CORS configured properly
- [ ] Rate limiting considered (add if needed)
- [ ] Input validation on forms
- [ ] Security headers configured

## Cost Estimation

**Vercel Free Tier includes:**
- Unlimited deployments
- 100GB bandwidth/month
- Automatic HTTPS
- DDoS protection
- 100 domains

**This is sufficient for demo site!**

If you exceed limits, Vercel Pro is $20/month.

---

## Quick Reference Commands

```bash
# Local testing
python application.py

# Push to deploy
git push origin main

# Check deployment status
vercel logs

# Rollback deployment
vercel rollback

# Check DNS propagation
dig stayscoutapp.com

# Generate secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

**Congratulations!** Your StayScout demo is now live at https://stayscoutapp.com

Ready for affiliate program applications and early user feedback!

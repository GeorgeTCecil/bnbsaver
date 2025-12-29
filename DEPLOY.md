# StayScout - Vercel Deployment Guide

Deploy StayScout to Vercel with custom domain `stayscoutapp.com` in 3 simple steps.

## Prerequisites

- [GitHub Account](https://github.com/signup) (free)
- [Vercel Account](https://vercel.com/signup) (free tier is sufficient)
- Domain `stayscoutapp.com` with DNS access

## Quick Deploy (3 Steps)

### Step 1: Push to GitHub

```bash
# Navigate to project directory
cd /mnt/c/Users/georg/OneDrive/Documents/git/bnbsaver/bnbsaver

# Add deployment files
git add application.py demo_results.py vercel.json requirements-vercel.txt .vercelignore templates/ static/

# Commit changes
git commit -m "Deploy StayScout to Vercel"

# Push to GitHub
git push origin main
```

**First time setup?** Create a GitHub repository first:

```bash
# 1. Create new repo on GitHub: https://github.com/new
#    Repository name: stayscout
#    Visibility: Public or Private (your choice)

# 2. Initialize and push
git init
git add application.py demo_results.py vercel.json requirements-vercel.txt .vercelignore templates/ static/
git commit -m "Initial commit - StayScout demo"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/stayscout.git
git push -u origin main
```

### Step 2: Deploy to Vercel

**Option A: Web Interface (Recommended)**

1. Visit [vercel.com/new](https://vercel.com/new)
2. Click **"Import Git Repository"**
3. Select your GitHub repository (`stayscout`)
4. Configure project settings:
   - **Framework Preset:** Other
   - **Root Directory:** `./` (leave as default)
   - **Build Command:** Leave empty
   - **Output Directory:** Leave empty
   - **Install Command:** Leave empty (auto-detected from requirements-vercel.txt)

5. **Add Environment Variables:**

   Click **"Environment Variables"** and add:

   ```
   Name: SECRET_KEY
   Value: [paste generated key - see command below]
   Environments: ✓ Production ✓ Preview ✓ Development
   ```

   ```
   Name: FLASK_ENV
   Value: production
   Environments: ✓ Production
   ```

   **Generate SECRET_KEY:**
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

   **Important:** Copy the generated key and use it as the SECRET_KEY value.

6. Click **"Deploy"**
7. Wait 1-2 minutes for deployment to complete
8. You'll receive a URL like: `https://stayscout.vercel.app` or `https://stayscout-xxx.vercel.app`

**Option B: Vercel CLI (Advanced Users)**

```bash
# Install Vercel CLI globally
npm install -g vercel

# Login to Vercel (opens browser)
vercel login

# Deploy to production
cd /mnt/c/Users/georg/OneDrive/Documents/git/bnbsaver/bnbsaver
vercel --prod

# Follow prompts to link to your GitHub repository
```

### Step 3: Connect Custom Domain

#### In Vercel Dashboard

1. Open your project in [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to **Settings** → **Domains**
3. Click **"Add Domain"**
4. Enter: `stayscoutapp.com`
5. Click **"Add"**
6. Repeat to add: `www.stayscoutapp.com`

Vercel will display the required DNS records to configure.

#### Configure DNS Records

At your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.), add these DNS records:

**For apex domain (`stayscoutapp.com`):**

```
Type:  A
Name:  @ (or leave blank)
Value: 76.76.21.21
TTL:   3600 (or Auto)
```

**For www subdomain (`www.stayscoutapp.com`):**

```
Type:  CNAME
Name:  www
Value: cname.vercel-dns.com
TTL:   3600 (or Auto)
```

**Alternative for apex domain (if A record doesn't work):**

Some registrars support ALIAS or ANAME records:

```
Type:  ALIAS or ANAME
Name:  @ (or leave blank)
Value: cname.vercel-dns.com
TTL:   3600 (or Auto)
```

#### Wait for DNS Propagation

- Typical time: 10-30 minutes
- Maximum time: 24-48 hours
- Check status in Vercel Dashboard (green checkmark when ready)

#### Verify Deployment

Visit your site:
- `https://stayscoutapp.com`
- `https://www.stayscoutapp.com`

Both should work with automatic HTTPS (SSL certificate).

**Done! Your site is live.**

---

## DNS Configuration by Registrar

### Namecheap

1. Login to [Namecheap](https://www.namecheap.com)
2. Dashboard → **Domain List**
3. Click **"Manage"** next to your domain
4. Go to **"Advanced DNS"** tab
5. Click **"Add New Record"** for each DNS record
6. Save all changes

### GoDaddy

1. Login to [GoDaddy](https://www.godaddy.com)
2. **My Products** → **Domains**
3. Click **"DNS"** next to your domain
4. Click **"Add"** to add each DNS record
5. Save changes

### Cloudflare

1. Login to [Cloudflare](https://dash.cloudflare.com)
2. Select your domain
3. Navigate to **DNS** → **Records**
4. Click **"Add record"** for each DNS entry
5. **Important:** Set Proxy Status to **"Proxied"** (orange cloud) for better security and performance
6. Save

### Google Domains

1. Login to [Google Domains](https://domains.google.com)
2. Select your domain
3. Go to **DNS** section
4. Scroll to **"Custom resource records"**
5. Add each DNS record
6. Save changes

### Other Registrars

The process is similar for all registrars:
1. Find the DNS management section
2. Add the A record for apex domain
3. Add the CNAME record for www subdomain
4. Save and wait for propagation

---

## Post-Deployment Checklist

After deployment, verify everything works:

- [ ] Visit `https://stayscoutapp.com` - loads correctly
- [ ] Visit `https://www.stayscoutapp.com` - loads correctly
- [ ] HTTPS enabled (green padlock in browser)
- [ ] Home page loads with demo data
- [ ] `/demo` page works
- [ ] `/about` page loads
- [ ] Navigation menu functions
- [ ] Images load correctly
- [ ] CSS styling applied
- [ ] Mobile responsive (test on phone)
- [ ] Test health endpoint: `https://stayscoutapp.com/health`

---

## Updating Your Deployed Site

Vercel automatically deploys when you push to GitHub:

```bash
# Make changes to your code
nano application.py  # or edit in VS Code

# Commit and push
git add .
git commit -m "Update feature description"
git push origin main
```

Vercel will:
1. Detect the GitHub push automatically
2. Build your project
3. Run tests (if configured)
4. Deploy to production
5. Update `stayscoutapp.com` within 1-2 minutes

**No manual deployment needed!**

---

## Environment Variables

### View Current Variables

1. Vercel Dashboard → Your Project
2. **Settings** → **Environment Variables**

### Add New Variable

1. Click **"Add New"**
2. Enter **Name** and **Value**
3. Select environments:
   - **Production:** Live site (stayscoutapp.com)
   - **Preview:** Pull request previews
   - **Development:** Local development with Vercel CLI
4. Click **"Save"**
5. **Redeploy** (Vercel will prompt you)

### Important Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `SECRET_KEY` | Random 64-char hex | Flask session security |
| `FLASK_ENV` | `production` | Sets production mode |

**Security Note:** Never commit `.env` files to GitHub. Always use Vercel's environment variable system.

---

## Monitoring & Logs

### View Deployment Logs

1. Vercel Dashboard → Your Project
2. Click **"Deployments"** tab
3. Click on any deployment
4. View **"Building"** and **"Function Logs"** tabs

### Real-time Logs (CLI)

```bash
# View live logs
vercel logs stayscout --follow

# View logs for specific deployment
vercel logs stayscout [deployment-url]
```

### Check Application Health

Health endpoint: `https://stayscoutapp.com/health`

Expected response:
```json
{
  "status": "healthy",
  "service": "StayScout Demo",
  "version": "1.0.0"
}
```

### Vercel Analytics (Optional)

Enable free analytics:
1. Vercel Dashboard → Your Project
2. **Analytics** tab
3. Click **"Enable"**

Provides:
- Page views
- Geographic data
- Device types
- Performance metrics

---

## Troubleshooting

### Build Fails

**Error:** `ModuleNotFoundError: No module named 'X'`

**Solution:**
1. Check that module is in `requirements-vercel.txt`
2. Test locally:
   ```bash
   pip install -r requirements-vercel.txt
   python application.py
   ```
3. Redeploy after fixing

---

### 404 Errors on Static Files

**Error:** Images, CSS not loading

**Solution:**
1. Verify folder structure:
   ```
   bnbsaver/
   ├── application.py
   ├── templates/
   │   └── *.html
   └── static/
       ├── css/
       ├── js/
       └── images/
   ```
2. Check `vercel.json` includes static file handling
3. Redeploy

---

### Domain Not Connecting

**Symptoms:** DNS_PROBE_FINISHED_NXDOMAIN or site not loading

**Solutions:**

1. **Verify DNS records exactly match Vercel's requirements**
   ```bash
   # Check DNS propagation (Linux/Mac)
   dig stayscoutapp.com

   # Check DNS (Windows)
   nslookup stayscoutapp.com
   ```

2. **Clear browser cache:**
   - Chrome: Ctrl+Shift+Del → Clear browsing data
   - Firefox: Ctrl+Shift+Del → Clear cache
   - Safari: Cmd+Option+E

3. **Wait longer:** DNS can take up to 48 hours (usually 10-30 min)

4. **Check Vercel Dashboard:**
   - Settings → Domains
   - Look for green checkmark next to domain
   - Red X means DNS not configured correctly

---

### Slow Performance

**Solutions:**

1. **Optimize images:**
   ```bash
   # Use compressed images (WebP format)
   # Maximum size: 500KB per image
   ```

2. **Enable caching:** Already configured in `vercel.json`

3. **Check Vercel region:** Configured to `iad1` (US East) in `vercel.json`

4. **Use Vercel Analytics** to identify slow pages

---

### Function Timeout

**Error:** `FUNCTION_INVOCATION_TIMEOUT`

**Solution:**
1. Free tier: 10 second max (configured in `vercel.json`)
2. Optimize slow database queries
3. Use caching for expensive operations
4. Consider upgrading to Pro ($20/mo) for 60s timeout

---

## Rollback to Previous Version

If deployment breaks something:

### Via Dashboard

1. **Deployments** tab
2. Find last working deployment
3. Click **"..."** menu
4. Select **"Promote to Production"**
5. Confirm

### Via CLI

```bash
# List recent deployments
vercel ls

# Promote specific deployment
vercel promote [deployment-url]
```

---

## Cost & Limits

### Vercel Free Tier (Hobby)

Perfect for StayScout demo:

- **Bandwidth:** 100 GB/month
- **Serverless Function Execution:** 100 GB-hours
- **Invocations:** 1,000,000/month
- **Deployments:** Unlimited
- **Domains:** 100 custom domains
- **Team size:** 1 user
- **SSL:** Automatic & free
- **DDoS protection:** Included
- **Global CDN:** Included

### When to Upgrade

Upgrade to **Vercel Pro** ($20/month) if:
- Traffic exceeds 100 GB/month
- Need longer function timeouts (60s vs 10s)
- Want team collaboration features
- Need advanced analytics

**For a demo/MVP, free tier is perfect!**

---

## Security Best Practices

### Implemented

- [x] HTTPS enforced automatically
- [x] Security headers configured (CSP, X-Frame-Options, etc.)
- [x] Environment variables secured (not in code)
- [x] `.gitignore` prevents committing secrets
- [x] `.vercelignore` excludes sensitive files
- [x] DDoS protection via Vercel
- [x] Automatic SSL certificate renewal

### Additional Recommendations

1. **Rotate SECRET_KEY periodically** (every 90 days)
2. **Enable Vercel Authentication** if site needs access control
3. **Monitor deployment logs** for suspicious activity
4. **Use Vercel's IP allowlist** for sensitive admin pages
5. **Keep dependencies updated** (check monthly)

---

## Testing Locally Before Deploy

Always test locally before pushing:

```bash
# Install dependencies
pip install -r requirements-vercel.txt

# Set environment variables
export SECRET_KEY="your-secret-key-here"
export FLASK_ENV="development"

# Run locally
python application.py

# Visit http://localhost:5000
```

Test all routes:
- `/` - Home page
- `/demo` - Demo page
- `/about` - About page
- `/health` - Health check

---

## Next Steps After Deployment

1. **Test Thoroughly**
   - Test all pages and features
   - Check mobile responsiveness
   - Verify forms work correctly
   - Test on different browsers

2. **SEO Setup**
   - Add `robots.txt`
   - Add `sitemap.xml`
   - Submit to Google Search Console
   - Submit to Bing Webmaster Tools

3. **Analytics**
   - Enable Vercel Analytics (free)
   - Optional: Add Google Analytics
   - Monitor traffic and errors

4. **Marketing**
   - Share on social media (Twitter, LinkedIn, Reddit)
   - Post on Product Hunt
   - Share on Hacker News
   - Email to beta users

5. **Affiliate Programs**
   - Apply for Airbnb affiliate program
   - Apply for Booking.com affiliate program
   - Apply for VRBO/Expedia affiliate program
   - Now you have a live demo to show!

6. **Gather Feedback**
   - Add feedback form
   - Create email list
   - Monitor user behavior
   - Iterate based on feedback

---

## Support & Resources

### Vercel Documentation
- **Official Docs:** https://vercel.com/docs
- **Python Guide:** https://vercel.com/docs/functions/serverless-functions/runtimes/python
- **Custom Domains:** https://vercel.com/docs/projects/domains

### Support Channels
- **Vercel Support:** https://vercel.com/support
- **Vercel Community:** https://github.com/vercel/vercel/discussions
- **Vercel Discord:** https://vercel.com/discord

### Flask Resources
- **Flask Docs:** https://flask.palletsprojects.com/
- **Flask Deployment:** https://flask.palletsprojects.com/en/stable/deploying/

---

## Quick Command Reference

```bash
# ========================================
# Local Development
# ========================================

# Install dependencies
pip install -r requirements-vercel.txt

# Run locally
python application.py

# Generate secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# ========================================
# Git & GitHub
# ========================================

# Stage changes
git add .

# Commit
git commit -m "Update description"

# Push (triggers auto-deploy)
git push origin main

# ========================================
# Vercel CLI
# ========================================

# Install CLI
npm install -g vercel

# Login
vercel login

# Deploy to production
vercel --prod

# View logs
vercel logs --follow

# List deployments
vercel ls

# ========================================
# DNS Testing
# ========================================

# Check DNS (Linux/Mac)
dig stayscoutapp.com
dig www.stayscoutapp.com

# Check DNS (Windows)
nslookup stayscoutapp.com
nslookup www.stayscoutapp.com

# Test with curl
curl -I https://stayscoutapp.com
```

---

## Summary

**3-Step Deployment:**
1. Push code to GitHub
2. Deploy via Vercel web interface
3. Configure DNS at your registrar

**Deployment time:** 10-15 minutes (plus DNS propagation)

**Ongoing updates:** Just `git push` - Vercel handles the rest!

---

**Congratulations! StayScout is now live at https://stayscoutapp.com**

Start gathering user feedback and building your waitlist!

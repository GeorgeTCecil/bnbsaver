# StayScout - Quick Start Deployment

**Deploy to Vercel in 3 commands + DNS setup**

## Files Ready

All deployment files are already created and configured:
- `vercel.json` - Vercel configuration (Python 3.11, security headers)
- `requirements-vercel.txt` - Minimal dependencies (Flask 3.1.0)
- `.vercelignore` - Excludes unnecessary files
- `.gitignore` - Prevents committing secrets
- `application.py` - Production-ready Flask app
- `demo_results.py` - Demo data
- `templates/` - HTML templates (6 files)
- `static/` - CSS and JS files

## 3-Command Deployment

```bash
# 1. Add and commit deployment files
git add application.py demo_results.py vercel.json requirements-vercel.txt .vercelignore templates/ static/
git commit -m "Deploy StayScout to Vercel"

# 2. Push to GitHub (triggers Vercel deployment if connected)
git push origin main

# 3. Generate SECRET_KEY for Vercel environment variables
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Vercel Web Setup (5 minutes)

1. **Import Project**
   - Go to https://vercel.com/new
   - Click "Import Git Repository"
   - Select your GitHub repository

2. **Configure Environment Variables**
   - Add `SECRET_KEY`: [paste output from command #3 above]
   - Add `FLASK_ENV`: `production`

3. **Deploy**
   - Click "Deploy"
   - Wait 1-2 minutes
   - Get your URL: `https://stayscout.vercel.app`

## DNS Configuration (10-30 minutes)

Add these records at your domain registrar:

**A Record (apex domain):**
```
Type:  A
Name:  @
Value: 76.76.21.21
TTL:   3600
```

**CNAME Record (www subdomain):**
```
Type:  CNAME
Name:  www
Value: cname.vercel-dns.com
TTL:   3600
```

**Connect in Vercel:**
1. Vercel Dashboard → Settings → Domains
2. Add `stayscoutapp.com`
3. Add `www.stayscoutapp.com`
4. Wait for green checkmarks (10-30 minutes)

## Verify Deployment

Test these URLs:
- https://stayscoutapp.com
- https://www.stayscoutapp.com
- https://stayscoutapp.com/health
- https://stayscoutapp.com/demo
- https://stayscoutapp.com/about

All should load with HTTPS (green padlock).

## Post-Deployment Checklist

- [ ] All pages load correctly
- [ ] HTTPS enabled on all pages
- [ ] Mobile responsive (test on phone)
- [ ] Images and CSS loading
- [ ] Health endpoint returns `{"status": "healthy"}`

## Continuous Deployment

After initial setup, updates are automatic:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main
# Vercel automatically deploys in 1-2 minutes
```

## Troubleshooting

**Build fails?**
- Check that all dependencies are in `requirements-vercel.txt`
- Test locally: `pip install -r requirements-vercel.txt && python application.py`

**Domain not working?**
- Wait 24-48 hours for DNS propagation (usually 10-30 min)
- Verify DNS: `nslookup stayscoutapp.com`

**404 errors?**
- Ensure `templates/` and `static/` folders are committed to git
- Check `vercel.json` routing configuration

## Support

- **Full guide:** See `DEPLOY.md` for detailed instructions
- **Summary:** See `DEPLOYMENT_SUMMARY.md` for configuration details
- **Vercel docs:** https://vercel.com/docs
- **Vercel support:** https://vercel.com/support

---

**Ready to deploy?** Run the 3 commands above and follow the Vercel web setup!

**Total deployment time:** 15-20 minutes + DNS propagation

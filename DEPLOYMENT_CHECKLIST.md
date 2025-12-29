# StayScout Deployment Checklist

## Pre-Deployment Verification

### Files Created ✓
- [x] `application.py` - Main Flask application
- [x] `demo_results.py` - Demo data (existing)
- [x] `vercel.json` - Vercel configuration
- [x] `requirements-demo.txt` - Minimal dependencies
- [x] `.vercelignore` - Deployment exclusions
- [x] `README_DEPLOY.md` - Deployment guide

### Templates Created ✓
- [x] `templates/base.html` - Base layout with navigation
- [x] `templates/home.html` - Landing page with demo preview
- [x] `templates/demo.html` - Interactive demo page
- [x] `templates/about.html` - About page
- [x] `templates/404.html` - Custom 404 page
- [x] `templates/500.html` - Custom error page

### Static Files Created ✓
- [x] `static/css/style.css` - Custom StayScout branding

## Deployment Steps

### 1. Repository Setup
```bash
# Navigate to project
cd /mnt/c/Users/georg/OneDrive/Documents/git/bnbsaver/bnbsaver

# Check git status
git status

# Add deployment files
git add application.py demo_results.py vercel.json requirements-demo.txt .vercelignore
git add templates/ static/ README_DEPLOY.md DEPLOYMENT_CHECKLIST.md

# Commit
git commit -m "Add StayScout production demo site for Vercel deployment"

# Push to GitHub
git push origin main
```

### 2. Vercel Deployment
- [ ] Log in to vercel.com
- [ ] Import GitHub repository
- [ ] Configure build settings:
  - Install Command: `pip install -r requirements-demo.txt`
  - Build Command: (leave empty)
  - Output Directory: (leave empty)
- [ ] Add environment variables:
  - `FLASK_ENV=production`
  - `SECRET_KEY=[generate secure key]`
- [ ] Click Deploy
- [ ] Wait for build to complete

### 3. Domain Configuration
- [ ] Add `stayscoutapp.com` in Vercel
- [ ] Add `www.stayscoutapp.com` in Vercel
- [ ] Configure DNS records at registrar:
  ```
  Type: A
  Name: @
  Value: 76.76.21.21

  Type: CNAME
  Name: www
  Value: cname.vercel-dns.com
  ```
- [ ] Wait for DNS propagation (10-30 minutes)
- [ ] Verify domain in Vercel
- [ ] Set primary domain to `stayscoutapp.com`

### 4. Post-Deployment Testing

#### Functionality Tests
- [ ] Home page loads (`https://stayscoutapp.com`)
- [ ] Demo page shows price comparisons
- [ ] About page displays correctly
- [ ] Navigation works across all pages
- [ ] Newsletter forms show alerts
- [ ] Early access forms work
- [ ] Mobile responsive on phone
- [ ] 404 page displays for invalid URLs
- [ ] All internal links work

#### Performance Tests
- [ ] Google PageSpeed score 90+
- [ ] Site loads in under 3 seconds
- [ ] Images load properly
- [ ] CSS styles applied correctly
- [ ] No console errors in browser

#### SEO Tests
- [ ] Meta descriptions present
- [ ] Open Graph tags working
- [ ] Title tags correct on all pages
- [ ] HTTPS enabled (green padlock)
- [ ] No mixed content warnings

### 5. Marketing Preparation

#### Content Verification
- [ ] Tagline correct: "Find the Best Price for Your Perfect Stay"
- [ ] All pricing data from demo displays properly
- [ ] Savings calculations show correctly ($500, 27%)
- [ ] Contact email updated (currently placeholder)
- [ ] Social media links added (if ready)

#### Analytics Setup (Optional)
- [ ] Enable Vercel Analytics
- [ ] Add Google Analytics (if using)
- [ ] Set up conversion tracking
- [ ] Configure Speed Insights

## Affiliate Program Applications

Once deployed and tested, you can apply to these programs:

### Priority Affiliate Programs
1. **VRBO/HomeAway Affiliate Program**
   - URL: https://www.vrbo.com/affiliate
   - Required: Live website, traffic stats
   - Commission: 4-5% per booking

2. **Booking.com Affiliate Partner Program**
   - URL: https://www.booking.com/affiliate
   - Required: Website with travel content
   - Commission: 25-40% commission

3. **Agoda Affiliate Program**
   - URL: https://www.agoda.com/affiliate
   - Required: Website or blog
   - Commission: Up to 7%

4. **Impact Radius / Rakuten**
   - Multiple vacation rental advertisers
   - Required: Professional website

### Application Tips
- Emphasize AI-powered price comparison
- Highlight user value proposition
- Show demo as proof of concept
- Include traffic projections
- Professional presentation matters

## Quick Commands Reference

```bash
# Generate secure secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Test DNS propagation
dig stayscoutapp.com
nslookup stayscoutapp.com

# View deployment logs (with Vercel CLI)
vercel logs

# Check git status
git status

# Deploy update
git add .
git commit -m "Update description"
git push origin main
```

## Troubleshooting

### Build Fails
**Check:**
- `requirements-demo.txt` is correct
- No syntax errors in `application.py`
- All templates exist in `templates/` folder

**Solution:**
```bash
# Test locally with minimal deps
pip install Flask==3.0.0 Werkzeug==3.0.1
python application.py
```

### Domain Not Working
**Check:**
- DNS records are correct
- 24-48 hours for full propagation
- Clear browser cache
- Try incognito mode

### Pages Not Loading
**Check:**
- `vercel.json` routes configuration
- Template files are named correctly
- No typos in route decorators

## Security Notes

- [x] No API keys in frontend
- [x] No sensitive data in repository
- [x] Environment variables in Vercel dashboard
- [x] HTTPS enabled automatically
- [x] No database (demo only)

## Performance Optimization

- [x] Minimal dependencies (Flask only)
- [x] No heavy AI libraries in demo
- [x] CDN for Bootstrap/icons
- [x] Optimized CSS (no bloat)
- [x] Static demo data (fast loading)

## Next Steps After Launch

1. **Monitor Performance**
   - Check Vercel analytics daily
   - Monitor uptime
   - Track visitor behavior

2. **Gather Feedback**
   - Share with friends/family
   - Post in relevant communities
   - Collect email signups

3. **Apply to Affiliate Programs**
   - Use live site as proof of concept
   - Emphasize unique value proposition
   - Professional communication

4. **Plan Full Product**
   - Backend API development
   - Real scraping integration
   - User authentication
   - Database setup
   - Payment processing

5. **Marketing Launch**
   - Social media announcement
   - Product Hunt launch
   - Travel communities
   - SEO optimization
   - Content marketing

## Success Metrics

**Week 1 Goals:**
- [ ] Site is live and stable
- [ ] 0 downtime
- [ ] Page load time < 3 seconds
- [ ] At least 100 visitors

**Month 1 Goals:**
- [ ] 1,000+ unique visitors
- [ ] 100+ email signups
- [ ] 1-2 affiliate approvals
- [ ] Positive user feedback

**Quarter 1 Goals:**
- [ ] 10,000+ visitors
- [ ] 500+ email signups
- [ ] 3+ affiliate partnerships
- [ ] Begin development of full product

## Contact & Support

- **Deployment Issues:** Check README_DEPLOY.md
- **Vercel Support:** https://vercel.com/support
- **Project Repository:** [Your GitHub URL]

---

**Ready to Deploy!** 🚀

Follow the steps above in order, and you'll have a professional demo site live at https://stayscoutapp.com in under an hour.

Good luck with your launch!

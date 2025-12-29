# StayScout Project Roadmap

## Overview
StayScout is an AI-powered vacation rental price comparison engine that helps travelers find the same properties across multiple booking platforms at the lowest price.

**Live Demo:** https://stayscoutapp.com
**Repository:** https://github.com/GeorgeTCecil/bnbsaver

---

## ✅ Phase 1: Foundation & Deployment (COMPLETED)

### Demo Site
- [x] Professional landing page with Bootstrap 5
- [x] Demo results showing real savings examples
- [x] Responsive design for mobile/desktop
- [x] Deploy to Vercel
- [x] Connect stayscoutapp.com domain

### Core Architecture
- [x] Multi-modal search design (text + image + AI verification)
- [x] AI modules: property extraction, search, verification, price extraction
- [x] Cost optimization: GPT-4o-mini for 99.4% profit margin ($0.003/search)
- [x] SerpAPI integration for text searches
- [x] Selenium/Chromium option for image searches

### Technical Stack
- [x] Flask web framework
- [x] LangChain for AI abstraction
- [x] OpenAI GPT-4o-mini
- [x] SerpAPI for Google searches
- [x] Vercel serverless deployment

---

## 🔄 Phase 2: Monetization Setup (IN PROGRESS)

### Affiliate Programs
- [ ] Sign up for Booking.com affiliate program (25% commission)
  - Category: **Comparison Engine**
  - URL: stayscoutapp.com
- [ ] Sign up for VRBO affiliate program
  - Category: **Comparison Engine**
  - URL: stayscoutapp.com
- [ ] Get affiliate tracking codes/IDs
- [ ] Test affiliate link conversions

### Revenue Model
- **Tier 1: Demo (Free)** - Pre-generated results, no API costs
- **Tier 2: Free Tier** - Limited searches (10/day), Selenium only
- **Tier 3: BYOK** - Bring Your Own API Keys, unlimited
- **Tier 4: Premium** - Full access, $0.49/search, 99.4% margin

---

## 📋 Phase 3: AI Affiliate Integration (NEXT)

### Exact Match Finder
```python
# Find the EXACT same property on affiliate sites
1. Extract property details from Airbnb listing
2. Generate search queries for Booking.com/VRBO
3. Use AI + image matching to verify it's the same property
4. Return affiliate link to exact match
```

**Files to create:**
- `affiliate_matcher.py` - Core matching logic
- `booking_com_searcher.py` - Booking.com specific search
- `vrbo_searcher.py` - VRBO specific search

### Similar Property Recommender
```python
# If no exact match, find similar cheaper alternatives
1. Extract key features: location, bedrooms, bathrooms, amenities, dates
2. Search for properties with matching features
3. AI ranks by similarity score
4. Show top 3 alternatives with savings estimate
```

**Benefits:**
- Increases conversion from 5% to 20-40%
- Even without exact match, user still books through your affiliate link
- More valuable to the user (backup options if property is booked)

**Files to create:**
- `similar_property_finder.py`
- `property_scorer.py` - AI similarity scoring

---

## 🧪 Phase 4: Testing & Optimization

### End-to-End Testing
- [ ] Test Airbnb scraping with 10+ different properties
- [ ] Test text search accuracy across booking sites
- [ ] Test image search with Selenium vs SerpAPI
- [ ] Test AI verification accuracy (95%+ target)
- [ ] Test price extraction from different booking sites
- [ ] Measure search time (target: under 15 seconds)

### Performance Optimization
- [ ] Cache search results (15 min TTL)
- [ ] Parallel API calls where possible
- [ ] Optimize AI prompts for speed
- [ ] Add progress indicators for long searches

---

## 🚀 Phase 5: Production Launch

### Full Site Features
- [ ] User accounts (optional, for saving searches)
- [ ] Search history
- [ ] Price alerts (notify when price drops)
- [ ] Multi-property comparison (compare 3-5 listings at once)
- [ ] Mobile app (React Native or PWA)

### Marketing & Growth
- [ ] SEO optimization (target keywords: "airbnb price comparison", "vacation rental deals")
- [ ] Blog content (travel tips, destination guides)
- [ ] Social media presence (Instagram, TikTok travel content)
- [ ] Partnerships with travel bloggers/influencers

### Analytics
- [ ] Google Analytics integration
- [ ] Track conversion rates by affiliate
- [ ] A/B test different UI layouts
- [ ] Monitor API costs vs revenue

---

## 📊 Success Metrics

### Technical KPIs
- Search completion rate: 95%+
- Search time: <15 seconds
- AI accuracy: 95%+
- Uptime: 99.9%

### Business KPIs
- Affiliate conversion rate: 20%+ (industry avg: 2-5%)
- Revenue per search: $0.49 (charged) - $0.003 (cost) = $0.487 profit
- Monthly users: Target 1,000 in first 3 months
- Monthly revenue: $1,000+ after 1,000 searches

---

## 💡 Future Ideas

### Advanced Features
- Multi-destination search (find cheapest city for beach vacation)
- Date flexibility (show cheaper dates for same property)
- Group bookings (optimize for large groups)
- Long-term rental search (monthly pricing comparison)

### Additional Revenue Streams
- Premium tier: Unlimited searches for $9.99/month
- White-label for travel agencies
- API access for other comparison sites
- Sponsored listings (booking sites pay for top placement)

---

## 🛠️ Current Tech Debt

### Known Issues
- Need error handling for properties not found
- Image search can be slow with Selenium
- Need retry logic for failed API calls
- Mobile UI needs polish

### Planned Refactoring
- Split multi_modal_search.py into smaller modules
- Add proper logging throughout
- Create unit tests for AI modules
- Add integration tests for search pipeline

---

## 📚 Documentation Needed

- [ ] API documentation (if offering API access)
- [ ] User guide (how to use StayScout)
- [ ] Developer setup guide (for contributors)
- [ ] Affiliate link disclosure (FTC compliance)

---

**Last Updated:** December 29, 2025
**Next Milestone:** Complete affiliate program signups and integrate affiliate links

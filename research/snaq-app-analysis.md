# SNAQ App Research Summary

## What is SNAQ?

SNAQ is an AI-powered diabetes food tracker available on:
- **Apple App Store**: 4.6/5 rating (2,413 reviews)
- **Google Play**: 4.1/5 rating (633 reviews)
- **Website**: snaq.ai
- **Pricing**: ~$100/year with 7-day free trial (premium, ad-free)

---

## 1. What Features Does SNAQ Have?

### Core Features:
- **Photo-Based Food Logging**: Snap a picture of food to get automatic nutritional breakdown (carbs, protein, fat, calories)
- **AI Food Recognition**: Uses computer vision to identify food items and estimate portions
- **CGM Integration**: Syncs with Dexcom, FreeStyle Libre, Contour, and other glucose sensors
- **Glucose & Time-in-Range Insights**: Tracks how specific foods impact blood sugar
- **Barcode Scanning**: For packaged foods
- **Voice Logging**: Add meals via voice input
- **Activity Tracking**: Syncs with fitness devices (Garmin, Whoop, Apple Watch, etc.)
- **Insulin Tracking**: Bolus insulin units can be displayed on glucose curves
- **Data Integration**: Apple Health, Nightscout
- **Provider Platform**: Healthcare professionals can view patient data
- **AI Coach**: Real-time support and meal insights

### Supported Devices:
- CGM: Dexcom, FreeStyle Libre, Contour, One Drop, Accu-Chek, One Touch
- Pens: Inpen (smart insulin pen)
- Activity: Garmin, Whoop, Apple Watch, Withings, Polar, Samsung

---

## 2. How Does It Work?

1. **Snap**: Take a photo of your meal
2. **Analyze**: AI estimates nutritional content and portion sizes
3. **Connect**: Sync CGM to see glucose impact
4. **Learn**: App learns your body's response patterns over 3+ days
5. **Track**: View historical patterns to understand food impacts

The app claims 5.5g mean absolute carbohydrate estimation error and 6.6% improvement in Time-in-Range based on clinical studies.

---

## 3. Strengths & Weaknesses

### Strengths:
✅ **Convenient photo-based logging** - eliminates manual entry  
✅ **CGM integration** - comprehensive glucose visualization  
✅ **Time-in-Range insights** - actionable pattern recognition  
✅ **Strong device ecosystem** - supports major CGMs, pens, fitness devices  
✅ **Clinical backing** - published studies support efficacy claims  
✅ **Provider platform** - enables healthcare team collaboration  
✅ **42% adherence rate** after 3 months (company data)  
✅ **AI Coach** - personalized real-time support  

### Weaknesses (from critical reviews):

❌ **AI Food Recognition is Unreliable** (Diabettech review):
- Failed to correctly identify basic foods (toast, biscuits, curry)
- Consistently underestimated portion sizes
- Struggled with non-plated meals (bowls, hands)
- Doesn't work well without LiDAR (iPhone 16 Pro/Pro Max only)
- Barcode scanning buried in menus, hard to find
- US-centric food database - poor for international users
- Users train the model FOR FREE while paying subscription

❌ **Subscription Cost**: ~$100/year is expensive for unreliable accuracy

❌ **Glucose Learning Delay**: Requires 3 days of data before providing estimates

❌ **Regional Limitations**: App explicitly states limited to US users for diabetes management

❌ **No transparency**: App doesn't admit when it doesn't recognize food - just gives wrong answers

---

## 4. What Does SNAQ NOT Do Well?

1. **Accurate carb counting** - especially for home-cooked, non-packaged meals
2. **Portion estimation** - consistently underestimates
3. **Non-plated meals** - only works well on a plate
4. **International food recognition** - US-centric database
5. **Branded/ packaged food recognition** - 50% hit rate even with visible packaging
6. **Recall previous meals** - doesn't remember user corrections well
7. **Transparent about limitations** - doesn't say "I don't know"
8. **Protein/fiber prioritization** - not focused on GLP-1 nutrition needs
9. **Medication tracking** - no injection scheduling or side effect logging
10. **Weight management** - not designed for weight loss tracking

---

## 5. How Could a GLP-1 Focused App Differentiate & Beat SNAQ?

### Target Audience Shift:
SNAQ targets **people with diabetes** (Type 1, Type 2). A GLP-1 app targets **weight loss patients** - a rapidly growing market (Ozempic, Wegovy, Mounjaro, Zepbound users).

### Differentiation Opportunities:

| Feature | SNAQ | GLP-1 App Opportunity |
|---------|------|----------------------|
| **Medication Tracking** | ❌ | ✅ Shot/pill reminders, dose tracking, medication level estimation |
| **Side Effect Logging** | ❌ | ✅ Nausea, fatigue, constipation tracking with trends |
| **Protein Focus** | ❌ | ✅ Priority tracking for muscle preservation during weight loss |
| **Fiber Tracking** | ❌ | ✅ Critical for GLP-1 GI side effect management |
| **Calorie Deficit** | ❌ | ✅ Calculate/maintain sustainable deficit |
| **Hydration** | ❌ | ✅ Track water intake (critical on GLP-1s) |
| **Injection Sites** | ❌ | ✅ Rotation tracking, site photos |
| **Dose Escalation** | ❌ | ✅ Timeline support for titration schedules |
| **Meal Timing** | ❌ | ✅ Optimize around injection schedule |
| **Satiety Tracking** | ❌ | ✅ Log hunger levels post-meals |

### Competitive Advantages:

1. **GLP-1 Specific Features**:
   - Medication reminders with half-life estimation
   - Side effect trend analysis
   - Titration schedule support
   - Injection site rotation tracking

2. **Better Nutrition Focus**:
   - Protein target alerts (prioritize 80-100g+ daily)
   - Fiber tracking (critical for GLP-1 users)
   - Hydration reminders
   - Meal size guidance based on medication effect

3. **Better Food Recognition**:
   - Partner with established food databases (like Cronometer)
   - Focus on accuracy over "AI" marketing
   - Be transparent about limitations
   - Include GLP-1 friendly recipe suggestions

4. **Better Pricing**:
   - Free tier with core features
   - Lower cost premium ($50-75/year vs $100)
   - Or freemium model with medication features free

5. **CGM Integration** (if using for metabolic health):
   - Many GLP-1 users use CGMs (Dexcom, Libre) for metabolic tracking
   - Show glucose stability patterns, not just food impact

### Key Takeaway:
SNAQ is a diabetes app that happens to do food tracking. A winning GLP-1 app would be a **weight loss/nutrition app** that happens to include medication management - focused on the unique needs of GLP-1 users (protein preservation, side effect management, hydration, sustainable eating patterns).

The GLP-1 market is exploding and currently underserved by specialized apps. Most GLP-1 users cobble together generic trackers (MyFitnessPal) with medication reminders (apps like Shotsy, Pep), but no comprehensive solution exists yet.

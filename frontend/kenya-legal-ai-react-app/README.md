# Kenya Legal AI

A comprehensive, multi-page React application for AI-powered legal research in Kenya.

## Features

- **Landing Page** - Premium marketing page with competitive comparison, features, testimonials, and pricing preview
- **Features Page** - Detailed feature breakdown with benefits
- **Pricing Page** - Three-tier pricing with FAQ accordion
- **Research Page** - Interactive AI chat interface with filters and example queries
- **About Page** - Company story, team, and values
- **Login/Signup** - Full authentication flows with role selection
- **Dashboard** - User dashboard with stats, recent queries, saved cases, and billing
- **Payment** - Checkout flow with card, M-Pesa, and bank transfer options

## Tech Stack

- React 18
- React Router v6
- Tailwind CSS
- Lucide React (icons)

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm start
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Project Structure

```
src/
  components/
    Layout.js          # Navbar, Footer, GlobalStyles
  pages/
    LandingPage.js     # Home/Marketing page
    FeaturesPage.js    # Feature details
    PricingPage.js     # Pricing & FAQ
    ResearchPage.js    # AI research chat
    AboutPage.js       # About us
    LoginPage.js       # Sign in
    SignupPage.js      # Sign up
    DashboardPage.js   # User dashboard
    PaymentPage.js     # Checkout
  App.js               # Main app with routing
  index.js             # Entry point
  index.css            # Tailwind + custom styles
```

## Design System

- **Primary Green**: `#2d5a47` (Kenya flag green)
- **Gold Accent**: `#d4af37` (Authority/trust)
- **Background**: `#faf9f6` (Parchment)
- **Typography**: Inter (sans) + Playfair Display (serif for headings)

## License

© 2026 Kenya Legal AI. All rights reserved.

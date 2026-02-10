import { NextRequest, NextResponse } from "next/server";

interface SubredditEntry {
  name: string;
  subscribers: number;
}

// Curated fallback list for when Reddit API blocks server-side requests
const POPULAR_SUBREDDITS: SubredditEntry[] = [
  { name: "SaaS", subscribers: 85000 },
  { name: "startups", subscribers: 1200000 },
  { name: "Entrepreneur", subscribers: 3500000 },
  { name: "smallbusiness", subscribers: 1800000 },
  { name: "marketing", subscribers: 1400000 },
  { name: "digital_marketing", subscribers: 350000 },
  { name: "SEO", subscribers: 450000 },
  { name: "socialmedia", subscribers: 380000 },
  { name: "content_marketing", subscribers: 120000 },
  { name: "growthacking", subscribers: 95000 },
  { name: "indiehackers", subscribers: 75000 },
  { name: "SideProject", subscribers: 140000 },
  { name: "webdev", subscribers: 2100000 },
  { name: "programming", subscribers: 6500000 },
  { name: "learnprogramming", subscribers: 4200000 },
  { name: "reactjs", subscribers: 410000 },
  { name: "nextjs", subscribers: 120000 },
  { name: "node", subscribers: 250000 },
  { name: "Python", subscribers: 2800000 },
  { name: "javascript", subscribers: 2600000 },
  { name: "typescript", subscribers: 180000 },
  { name: "devops", subscribers: 350000 },
  { name: "aws", subscribers: 380000 },
  { name: "technology", subscribers: 15000000 },
  { name: "ProductManagement", subscribers: 95000 },
  { name: "product_design", subscribers: 45000 },
  { name: "UserExperience", subscribers: 280000 },
  { name: "UI_Design", subscribers: 120000 },
  { name: "freelance", subscribers: 310000 },
  { name: "WorkOnline", subscribers: 650000 },
  { name: "remotework", subscribers: 180000 },
  { name: "digitalnomad", subscribers: 2200000 },
  { name: "passive_income", subscribers: 550000 },
  { name: "ecommerce", subscribers: 280000 },
  { name: "dropship", subscribers: 180000 },
  { name: "shopify", subscribers: 220000 },
  { name: "Affiliatemarketing", subscribers: 160000 },
  { name: "copywriting", subscribers: 240000 },
  { name: "emailmarketing", subscribers: 45000 },
  { name: "analytics", subscribers: 85000 },
  { name: "datascience", subscribers: 1800000 },
  { name: "MachineLearning", subscribers: 2800000 },
  { name: "artificial", subscribers: 1200000 },
  { name: "ChatGPT", subscribers: 5000000 },
  { name: "LocalLLaMA", subscribers: 350000 },
  { name: "OpenAI", subscribers: 1500000 },
  { name: "ArtificialIntelligence", subscribers: 950000 },
  { name: "crypto", subscribers: 3800000 },
  { name: "personalfinance", subscribers: 18000000 },
  { name: "investing", subscribers: 3200000 },
  { name: "stocks", subscribers: 6500000 },
  { name: "fintech", subscribers: 55000 },
  { name: "nocode", subscribers: 65000 },
  { name: "lowcode", subscribers: 18000 },
  { name: "Automation", subscribers: 85000 },
  { name: "webdesign", subscribers: 680000 },
  { name: "graphic_design", subscribers: 3200000 },
  { name: "design", subscribers: 1100000 },
  { name: "gaming", subscribers: 35000000 },
  { name: "games", subscribers: 3500000 },
  { name: "IndieGaming", subscribers: 280000 },
  { name: "gamedev", subscribers: 850000 },
  { name: "fitness", subscribers: 11000000 },
  { name: "nutrition", subscribers: 3800000 },
  { name: "loseit", subscribers: 4500000 },
  { name: "running", subscribers: 2800000 },
  { name: "bodybuilding", subscribers: 2200000 },
  { name: "meditation", subscribers: 1400000 },
  { name: "selfimprovement", subscribers: 2200000 },
  { name: "productivity", subscribers: 1200000 },
  { name: "GetMotivated", subscribers: 19000000 },
  { name: "books", subscribers: 24000000 },
  { name: "writing", subscribers: 2800000 },
  { name: "screenwriting", subscribers: 1200000 },
  { name: "photography", subscribers: 6500000 },
  { name: "videography", subscribers: 280000 },
  { name: "youtube", subscribers: 1100000 },
  { name: "NewTubers", subscribers: 350000 },
  { name: "Twitch", subscribers: 1400000 },
  { name: "podcasting", subscribers: 280000 },
  { name: "music", subscribers: 33000000 },
  { name: "WeAreTheMusicMakers", subscribers: 2200000 },
  { name: "foodhacks", subscribers: 1200000 },
  { name: "cooking", subscribers: 4500000 },
  { name: "travel", subscribers: 8500000 },
  { name: "education", subscribers: 280000 },
  { name: "Teachers", subscribers: 550000 },
  { name: "college", subscribers: 950000 },
  { name: "cscareerquestions", subscribers: 850000 },
  { name: "jobs", subscribers: 280000 },
  { name: "careerguidance", subscribers: 550000 },
  { name: "resumes", subscribers: 280000 },
  { name: "AskReddit", subscribers: 47000000 },
  { name: "todayilearned", subscribers: 33000000 },
  { name: "explainlikeimfive", subscribers: 23000000 },
  { name: "LifeProTips", subscribers: 22000000 },
  { name: "InternetIsBeautiful", subscribers: 17000000 },
  { name: "Futurology", subscribers: 19000000 },
  { name: "space", subscribers: 23000000 },
  { name: "science", subscribers: 31000000 },
  { name: "gadgets", subscribers: 20000000 },
  { name: "Android", subscribers: 4500000 },
  { name: "apple", subscribers: 5500000 },
  { name: "iphone", subscribers: 5000000 },
  { name: "linux", subscribers: 1200000 },
  { name: "opensource", subscribers: 180000 },
  { name: "privacy", subscribers: 2800000 },
  { name: "cybersecurity", subscribers: 550000 },
  { name: "netsec", subscribers: 550000 },
  { name: "hacking", subscribers: 2800000 },
  { name: "legaladvice", subscribers: 3500000 },
  { name: "RealEstate", subscribers: 950000 },
  { name: "realestateinvesting", subscribers: 450000 },
  { name: "landlord", subscribers: 85000 },
  { name: "InteriorDesign", subscribers: 4500000 },
  { name: "HomeImprovement", subscribers: 4500000 },
  { name: "DIY", subscribers: 23000000 },
  { name: "buildapc", subscribers: 5500000 },
  { name: "hardware", subscribers: 180000 },
  { name: "sysadmin", subscribers: 850000 },
  { name: "homelab", subscribers: 1200000 },
  { name: "networking", subscribers: 550000 },
  { name: "database", subscribers: 85000 },
  { name: "SQL", subscribers: 180000 },
  { name: "docker", subscribers: 280000 },
  { name: "kubernetes", subscribers: 280000 },
  { name: "golang", subscribers: 280000 },
  { name: "rust", subscribers: 350000 },
  { name: "csharp", subscribers: 280000 },
  { name: "java", subscribers: 350000 },
  { name: "swift", subscribers: 120000 },
  { name: "FlutterDev", subscribers: 180000 },
  { name: "reactnative", subscribers: 120000 },
  { name: "AndroidDev", subscribers: 220000 },
  { name: "iOSProgramming", subscribers: 120000 },
  { name: "bioinformatics", subscribers: 120000 },
  { name: "compsci", subscribers: 280000 },
  { name: "AskEngineers", subscribers: 550000 },
  { name: "engineering", subscribers: 550000 },
  { name: "electronics", subscribers: 550000 },
  { name: "robotics", subscribers: 280000 },
  { name: "3Dprinting", subscribers: 1200000 },
  { name: "MicroSaaS", subscribers: 25000 },
  { name: "EntrepreneurRideAlong", subscribers: 180000 },
  { name: "juststart", subscribers: 55000 },
  { name: "SaaSMarketing", subscribers: 8000 },
  { name: "SaaSSales", subscribers: 5000 },
  { name: "GrowthHacking", subscribers: 95000 },
  { name: "DigitalMarketing", subscribers: 350000 },
  { name: "PPC", subscribers: 55000 },
  { name: "bigseo", subscribers: 85000 },
  { name: "TechStartups", subscribers: 15000 },
];

function searchFallback(query: string): SubredditEntry[] {
  const lower = query.toLowerCase();
  return POPULAR_SUBREDDITS
    .filter((s) => s.name.toLowerCase().includes(lower))
    .sort((a, b) => b.subscribers - a.subscribers)
    .slice(0, 10);
}

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get("q");

  if (!query || query.length < 2) {
    return NextResponse.json({ data: { children: [] } });
  }

  try {
    // Try Reddit API first
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);

    const response = await fetch(
      `https://www.reddit.com/subreddits/search.json?q=${encodeURIComponent(query)}&limit=10&raw_json=1`,
      {
        headers: {
          "User-Agent": "web:bc-rao:v1.0.0 (by /u/bc-rao-app)",
        },
        signal: controller.signal,
      }
    );

    clearTimeout(timeout);

    if (response.ok) {
      const data = await response.json();
      const children = data?.data?.children || [];

      // If Reddit returned results, use them
      if (children.length > 0) {
        return NextResponse.json(data);
      }
    }
  } catch {
    // Reddit API failed or timed out — fall through to fallback
  }

  // Fallback: search curated list
  const fallbackResults = searchFallback(query);
  const children = fallbackResults.map((s) => ({
    kind: "t5",
    data: {
      display_name: s.name,
      subscribers: s.subscribers,
    },
  }));

  return NextResponse.json({ data: { children } });
}

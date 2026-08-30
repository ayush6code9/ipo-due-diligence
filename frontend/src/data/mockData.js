// Centralized mock data for Phase 2 (frontend UI only).
//
// Shape is deliberately close to what the real backend will eventually
// return (see SRS Module 9 / Module 10) so that wiring up real API calls
// in a later phase mostly means swapping the data source, not the
// component props.

export const searchableIpos = [
  { id: 'apex-industrial', name: 'Apex Industrial Components Ltd', sector: 'Industrial Manufacturing', status: 'Open' },
  { id: 'northgate-logistics', name: 'Northgate Logistics Ltd', sector: 'Logistics & Supply Chain', status: 'Upcoming' },
  { id: 'brightleaf-foods', name: 'Brightleaf Foods Ltd', sector: 'Consumer Staples', status: 'Closed' },
  { id: 'veyra-diagnostics', name: 'Veyra Diagnostics Ltd', sector: 'Healthcare Diagnostics', status: 'Upcoming' },
]

// Every entry above resolves to this single fully-worked example for the
// Phase 2 demo — only one IPO needs complete mock data to show the dashboard.
export const mockIpo = {
  id: 'apex-industrial',
  companyName: 'Apex Industrial Components Ltd',
  sector: 'Industrial Manufacturing',
  overview:
    'Apex Industrial Components manufactures precision-machined parts for the automotive and heavy-equipment industries, supplying both domestic and export customers from three facilities in Gujarat and Tamil Nadu.',

  overallAssessment: {
    score: 84,
    maxScore: 100,
    label: 'Financially Strong',
    level: 'strong', // strong | moderate | high-risk — drives status color
  },

  riskLevel: { label: 'Medium', level: 'moderate' },
  promoterQuality: { label: 'Good', level: 'strong', stars: 4, maxStars: 5 },
  marketInterest: { label: 'High', level: 'strong' },

  ipoParameters: {
    issueSize: '₹1,240 Cr',
    priceBand: '₹412 – ₹434',
    lotSize: '34 shares',
    minInvestment: '₹14,756',
    openDate: '18 Aug 2026',
    closeDate: '21 Aug 2026',
    freshIssue: '₹740 Cr',
    offerForSale: '₹500 Cr',
  },

  gmp: {
    value: '₹38',
    percentOfCap: '8.8%',
    lastUpdated: '18 Aug 2026, 9:40 AM',
    note:
      'Grey Market Premium is an unofficial, unregulated indicator of listing-day demand. It can change daily and is not a guarantee of listing gains.',
  },

  subscription: {
    lastUpdated: '18 Aug 2026, 6:00 PM · Day 1',
    retail: 1.8,
    nii: 2.3,
    qib: 0.6,
    overall: 1.6,
  },

  financialHealth: {
    score: 84,
    maxScore: 100,
    status: 'Strong',
    level: 'strong',
    reasons: [
      'Revenue has grown consistently over the last three years',
      'The company has been profitable in each of the last three years',
      'Debt is under control compared to similar companies',
      'Cash flow from operations is healthy and positive',
    ],
  },

  financialMetrics: [
    {
      key: 'revenueGrowth',
      label: 'Revenue Growth',
      value: '18.4%',
      trend: 'up',
      meaning: 'Sales have grown by this much compared to last year — a sign the business is expanding.',
      learnMore:
        'Revenue growth alone doesn’t guarantee profit — it’s worth checking this alongside profit margin to see if growth is actually translating into earnings.',
    },
    {
      key: 'profitMargin',
      label: 'Profit Margin',
      value: '12.1%',
      trend: 'up',
      meaning: 'Out of every ₹100 in sales, the company keeps about ₹12 as profit after all expenses.',
      learnMore:
        'Profit margins vary a lot by industry, so this is most meaningful when compared with similar companies rather than in isolation.',
    },
    {
      key: 'debtToEquity',
      label: 'Debt-to-Equity',
      value: '0.42',
      trend: 'flat',
      meaning: 'Shows how much the company relies on borrowed money compared with shareholders’ money. Below 1 is generally considered manageable.',
      learnMore:
        'A very low ratio isn’t automatically better — some borrowing can help a company grow faster. Extremely high ratios are the bigger warning sign.',
    },
    {
      key: 'roe',
      label: 'ROE (Return on Equity)',
      value: '21.3%',
      trend: 'up',
      meaning: 'Shows how efficiently the company uses shareholders’ money to generate profit. Higher is generally better.',
      learnMore:
        'A high ROE driven mainly by heavy borrowing (rather than genuine efficiency) can be misleading, so it’s worth reading alongside Debt-to-Equity.',
    },
    {
      key: 'roa',
      label: 'ROA (Return on Assets)',
      value: '9.7%',
      trend: 'flat',
      meaning: 'Shows how efficiently the company uses everything it owns — factories, equipment, cash — to generate profit.',
      learnMore:
        'Asset-heavy industries like manufacturing typically show lower ROA than asset-light businesses like software — compare within the same sector.',
    },
  ],

  risks: [
    {
      category: 'Business Risk',
      severity: 'Medium',
      level: 'moderate',
      reason: 'The company depends heavily on a small number of large customers for a significant share of its revenue.',
      impact: 'If a major customer reduces orders or leaves, future revenue could decline noticeably.',
    },
    {
      category: 'Legal Risk',
      severity: 'Low',
      level: 'strong',
      reason: 'No material litigation was identified in the sections of the document that were analysed.',
      impact: 'Low expected impact on operations or finances at this time.',
    },
    {
      category: 'Industry Risk',
      severity: 'Medium',
      level: 'moderate',
      reason: 'The industrial components sector is competitive, with several established players in the same segment.',
      impact: 'Pricing pressure could affect margins if competition intensifies.',
    },
    {
      category: 'Financial Risk',
      severity: 'Low',
      level: 'strong',
      reason: 'Debt levels are moderate and interest obligations are comfortably covered by operating profit.',
      impact: 'Low near-term risk to financial stability.',
    },
  ],

  promoter: {
    stars: 4,
    maxStars: 5,
    label: 'Good',
    level: 'strong',
    points: [
      'Promoters have over 15 years of combined experience in industrial manufacturing',
      'Promoters continue to hold a significant ownership stake after the offer',
      'No history of regulatory action identified in the analysed document',
    ],
    litigation: {
      present: true,
      note: 'One disclosed litigation matter relating to a commercial contract dispute, currently pending.',
    },
  },

  topStrengths: [
    'Revenue and profit have grown steadily for three consecutive years',
    'Healthy, positive cash flow from core operations',
    'Debt levels are manageable relative to peers',
  ],

  topRisks: [
    'Revenue is concentrated among a small number of large customers',
    'Operates in a competitive industry with established players',
    'Valuation is at the higher end compared to some listed peers',
  ],

  charts: {
    revenue: [
      { year: 'FY23', value: 812 },
      { year: 'FY24', value: 958 },
      { year: 'FY25', value: 1134 },
    ],
    profit: [
      { year: 'FY23', value: 74 },
      { year: 'FY24', value: 96 },
      { year: 'FY25', value: 137 },
    ],
    debt: [
      { year: 'FY23', value: 0.61 },
      { year: 'FY24', value: 0.51 },
      { year: 'FY25', value: 0.42 },
    ],
  },

  aiSummary:
    'This company has shown steady revenue and profit growth over the last three years. Its debt is relatively low and the promoters have relevant industry experience. The biggest concern is customer concentration, because a significant portion of revenue depends on a small number of customers. Overall, the company appears financially healthy, but investors should understand these risks before making a decision.',

  chatSuggestions: [
    'What are the biggest risks?',
    'How is the company making money?',
    'Who are the promoters?',
  ],
}

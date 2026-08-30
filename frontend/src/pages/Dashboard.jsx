import { useLocation } from 'react-router-dom'
import Layout from '../components/common/Layout'
import SectionHeading from '../components/common/SectionHeading'
import DashboardHeader from '../components/dashboard/DashboardHeader'
import DashboardNav from '../components/dashboard/DashboardNav'
import OverallAssessment from '../components/dashboard/OverallAssessment'
import TopStrengthsRisks from '../components/dashboard/TopStrengthsRisks'
import AISummaryCard from '../components/dashboard/AISummaryCard'
import DownloadReportButton from '../components/dashboard/DownloadReportButton'
import IPOParametersCard from '../components/market/IPOParametersCard'
import MarketDataSection from '../components/market/MarketDataSection'
import FinancialHealthCard from '../components/financial/FinancialHealthCard'
import FinancialMetricsGrid from '../components/financial/FinancialMetricsGrid'
import RiskSection from '../components/risk/RiskSection'
import PromoterQualityCard from '../components/promoter/PromoterQualityCard'
import ChartsSection from '../components/charts/ChartsSection'
import ChatPanel from '../components/chat/ChatPanel'
import { mockIpo } from '../data/mockData'

/**
 * Transform backend analysis data to the shape the existing dashboard
 * components expect. This keeps all the existing components unchanged.
 */
function transformAnalysis(analysis) {
  if (!analysis) return null

  const fa = analysis.financial_health || {}
  const ra = analysis.risk_analysis || {}
  const pa = analysis.promoter_analysis || {}
  const oa = analysis.overall_assessment || {}

  return {
    id: `doc-${analysis.document_id}`,
    companyName: analysis.company_name || 'Uploaded DRHP',
    sector: analysis.sector || 'N/A',
    overview: analysis.overview || '',

    overallAssessment: {
      score: oa.score ?? 0,
      maxScore: oa.max_score ?? 100,
      label: oa.label || 'Unavailable',
      level: oa.level || 'moderate',
    },

    riskLevel: analysis.risk_level || { label: 'Medium', level: 'moderate' },
    promoterQuality: {
      label: (analysis.promoter_quality_summary || {}).label || 'Unavailable',
      level: (analysis.promoter_quality_summary || {}).level || 'moderate',
      stars: pa.stars ?? 0,
      maxStars: pa.max_stars ?? 5,
    },
    marketInterest: analysis.market_interest || { label: 'Unavailable', level: 'moderate' },

    ipoParameters: analysis.ipo_parameters || {},

    gmp: {
      value: 'Unavailable',
      percentOfCap: '—',
      lastUpdated: '—',
      note: 'Grey Market Premium data is not available for uploaded DRHPs. GMP is an unofficial, unregulated indicator and is not a guarantee of listing gains.',
    },

    subscription: {
      lastUpdated: '—',
      retail: null,
      nii: null,
      qib: null,
      overall: null,
    },

    financialHealth: {
      score: fa.score ?? null,
      maxScore: fa.max_score ?? 100,
      status: fa.status || 'Unavailable',
      level: fa.level || 'moderate',
      reasons: fa.reasons || [],
    },

    financialMetrics: (analysis.financial_metrics || []).map((m) => ({
      key: m.key,
      label: m.label,
      value: m.value,
      trend: m.trend,
      meaning: m.meaning,
      learnMore: m.learn_more,
    })),

    risks: (ra.risks || []).map((r) => ({
      category: r.category,
      severity: r.severity,
      level: r.level,
      reason: r.reason,
      impact: r.impact,
    })),

    promoter: {
      stars: pa.stars ?? 0,
      maxStars: pa.max_stars ?? 5,
      label: pa.label || 'Unavailable',
      level: pa.level || 'moderate',
      points: pa.points || [],
      litigation: {
        present: pa.litigation_present ?? false,
        note: pa.litigation_note || 'No litigation information available.',
      },
    },

    topStrengths: analysis.top_strengths || [],
    topRisks: analysis.top_risks || [],

    charts: analysis.charts || { revenue: [], profit: [], debt: [] },

    aiSummary: analysis.ai_summary || 'AI summary is not available. Configure GEMINI_API_KEY in .env to enable AI-generated summaries.',

    chatSuggestions: [
      'What are the biggest risks?',
      'How does the company make money?',
      'Who are the promoters?',
      'How has revenue changed?',
      'Does the company have significant debt?',
    ],
  }
}

export default function Dashboard() {
  const location = useLocation()
  const documentId = location.state?.documentId ?? null
  const analysisData = location.state?.analysis ?? null

  // Use real data if available, fall back to mock
  const ipo = analysisData ? transformAnalysis(analysisData) : mockIpo

  return (
    <Layout>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
        <DashboardHeader ipo={ipo} />

        <div className="flex gap-10">
          <DashboardNav />

          <div className="flex-1 min-w-0 space-y-12">
            <section id="overview" className="scroll-mt-24">
              <OverallAssessment ipo={ipo} />
            </section>

            <section>
              <SectionHeading id="ipo-parameters" index={1} title="Important IPO Parameters" />
              <IPOParametersCard params={ipo.ipoParameters} />
            </section>

            <section>
              <SectionHeading
                id="market-data"
                index={2}
                title="GMP & Subscription Status"
                subtitle="External market indicators — unofficial, and updated separately from the DRHP itself."
              />
              <MarketDataSection gmp={ipo.gmp} subscription={ipo.subscription} />
            </section>

            <section>
              <SectionHeading id="financial-health" index={3} title="Financial Health" />
              <FinancialHealthCard health={ipo.financialHealth} />
            </section>

            <section>
              <SectionHeading
                id="financial-metrics"
                index={4}
                title="Financial Metrics"
                subtitle="Every number here is followed by what it actually means."
              />
              <FinancialMetricsGrid metrics={ipo.financialMetrics} />
            </section>

            <section>
              <SectionHeading id="risk-analysis" index={5} title="Risk Analysis" />
              <RiskSection risks={ipo.risks} />
            </section>

            <section>
              <SectionHeading id="promoter-quality" index={6} title="Promoter Quality" />
              <PromoterQualityCard promoter={ipo.promoter} />
            </section>

            <section>
              <SectionHeading id="strengths-risks" index={7} title="Strengths & Risks, at a Glance" />
              <TopStrengthsRisks strengths={ipo.topStrengths} risks={ipo.topRisks} />
            </section>

            <section>
              <SectionHeading id="charts" index={8} title="Charts" subtitle="Financial history, simplified." />
              <ChartsSection charts={ipo.charts} />
            </section>

            <section>
              <SectionHeading id="ai-summary" index={9} title="AI Summary" />
              <AISummaryCard summary={ipo.aiSummary} />
            </section>

            <section>
              <SectionHeading id="chat" index={10} title="Chat with DRHP" />
              <ChatPanel suggestions={ipo.chatSuggestions} documentId={documentId} />
            </section>

            <section id="download-report" className="scroll-mt-24">
              <DownloadReportButton documentId={documentId} />
            </section>
          </div>
        </div>
      </div>
    </Layout>
  )
}

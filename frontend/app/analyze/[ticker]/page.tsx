'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { StockScore } from '@/types';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { AlertCircle, CheckCircle2, TrendingUp, DollarSign, Activity } from 'lucide-react';

export default function AnalysisPage() {
    const { ticker } = useParams();
    const [data, setData] = useState<StockScore | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!ticker) return;

        const fetchData = async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/analyze/${ticker}`);
                if (!res.ok) throw new Error('Failed to fetch data');
                const json = await res.json();
                setData(json);

                if (typeof window !== 'undefined') {
                    const saved = localStorage.getItem('stock_history');
                    let history = saved ? JSON.parse(saved) : [];
                    history = history.filter((h: any) => h.ticker !== json.ticker);
                    history.unshift({
                        ticker: json.ticker,
                        score: json.total_score,
                        date: new Date().toISOString()
                    });
                    if (history.length > 10) history.pop();
                    localStorage.setItem('stock_history', JSON.stringify(history));
                }
            } catch (err) {
                setError('Analysis failed. Please check the ticker code.');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [ticker]);

    if (loading) return <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">Loading...</div>;
    if (error) return <div className="min-h-screen flex items-center justify-center bg-gray-900 text-red-400">{error}</div>;
    if (!data) return null;

    const { total_score, breakdown, financial_data } = data;

    // Format data for charts
    const chartData = financial_data.fiscal_years.map((year, i) => ({
        year,
        income: financial_data.ordinary_income[i],
        eps: financial_data.eps[i],
        operating_cf: financial_data.operating_cf[i],
    }));

    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-green-400';
        if (score >= 50) return 'text-yellow-400';
        return 'text-red-400';
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white p-8">
            <div className="max-w-7xl mx-auto space-y-8">
                {/* Header */}
                <header className="flex justify-between items-center border-b border-gray-800 pb-4">
                    <div>
                        <h1 className="text-4xl font-bold">{data.ticker} Analysis</h1>
                        <p className="text-gray-400">Financial Health & Profitability</p>
                    </div>
                    <div className="text-center">
                        <div className="text-sm text-gray-400">Total Score</div>
                        <div className={`text-6xl font-black ${getScoreColor(total_score)}`}>
                            {total_score}
                        </div>
                    </div>
                </header>

                {/* Detailed Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <ScoreCard label="Ordinary Income Trend" score={breakdown.ordinary_income} icon={<TrendingUp />} />
                    <ScoreCard label="EPS Trend" score={breakdown.eps} icon={<DollarSign />} />
                    <ScoreCard label="Total Assets Trend" score={breakdown.total_assets} icon={<Activity />} />
                    <ScoreCard label="Operating CF" score={breakdown.operating_cf} icon={<Activity />} />
                    <ScoreCard label="Cash Trend" score={breakdown.cash_equivalents} icon={<DollarSign />} />
                    <ScoreCard label="ROE (>=7%)" score={breakdown.roe} icon={<TrendingUp />} />
                    <ScoreCard label="Equity Ratio (>=50%)" score={breakdown.equity_ratio} icon={<Activity />} />
                    <ScoreCard label="Dividend Safety" score={breakdown.dividend} icon={<DollarSign />} />
                </div>

                {/* Charts Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="bg-gray-800 p-6 rounded-xl">
                        <h3 className="text-xl font-bold mb-4">Financial Trends (Income & CF)</h3>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                    <XAxis dataKey="year" stroke="#9CA3AF" />
                                    <YAxis stroke="#9CA3AF" />
                                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none' }} />
                                    <Line type="monotone" dataKey="income" stroke="#60A5FA" name="Ord. Income" />
                                    <Line type="monotone" dataKey="operating_cf" stroke="#34D399" name="Op. CF" />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="bg-gray-800 p-6 rounded-xl">
                        <h3 className="text-xl font-bold mb-4">EPS Trend</h3>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                    <XAxis dataKey="year" stroke="#9CA3AF" />
                                    <YAxis stroke="#9CA3AF" />
                                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none' }} />
                                    <Line type="monotone" dataKey="eps" stroke="#F472B6" strokeWidth={2} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

                {/* TradingView Widget (Placeholder/Iframe) */}
                <div className="bg-gray-800 p-6 rounded-xl">
                    <h3 className="text-xl font-bold mb-4">Stock Price Chart</h3>
                    <div className="h-96 w-full">
                        {/* Simple Iframe to TradingView Symbol Overview */}
                        <iframe
                            scrolling="no"
                            allowTransparency={true}
                            frameBorder="0"
                            src={`https://s.tradingview.com/widgetembed/?frameElementId=tradingview_widget&symbol=${ticker}&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=Asia%2FTokyo`}
                            style={{ boxSizing: 'border-box', height: '100%', width: '100%' }}
                        ></iframe>
                    </div>
                </div>

            </div>
        </div>
    );
}

function ScoreCard({ label, score, icon }: { label: string, score: number, icon: React.ReactNode }) {
    const passed = score > 0;
    return (
        <div className={`p-4 rounded-lg border ${passed ? 'border-green-500/30 bg-green-500/10' : 'border-red-500/30 bg-red-500/10'} flex items-center justify-between`}>
            <div className="flex items-center gap-3">
                <div className={`${passed ? 'text-green-400' : 'text-red-400'}`}>
                    {icon}
                </div>
                <div>
                    <h4 className="font-semibold text-sm">{label}</h4>
                    <p className={`text-xs ${passed ? 'text-green-400' : 'text-red-400'}`}>
                        {passed ? 'Passed (+12.5)' : 'Failed (0)'}
                    </p>
                </div>
            </div>
            <div>
                {passed ? <CheckCircle2 className="text-green-400 w-6 h-6" /> : <AlertCircle className="text-red-400 w-6 h-6" />}
            </div>
        </div>
    )
}

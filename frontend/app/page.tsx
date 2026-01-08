'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [ticker, setTicker] = useState('');
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker) {
      router.push(`/analyze/${ticker}`);
    }
  };

  const [history, setHistory] = useState<any[]>([]);

  // Load history on mount
  useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('stock_history');
      if (saved) setHistory(JSON.parse(saved));
    }
  });

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-900 text-white p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm lg:flex flex-col">
        <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 text-transparent bg-clip-text mb-8">
          Stock Strongest Analysis
        </h1>
        <p className="text-xl text-gray-400 mb-12">
          Visualize Financial Health & Profitability in Seconds
        </p>

        <form onSubmit={handleSearch} className="w-full max-w-md flex flex-col gap-4 mb-16">
          <input
            type="text"
            placeholder="Enter Stock Code (e.g. 7203)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            className="p-4 rounded-lg bg-gray-800 border border-gray-700 focus:border-blue-500 focus:outline-none text-2xl text-center"
          />
          <button
            type="submit"
            className="p-4 rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors font-bold text-xl"
          >
            Analyze
          </button>
        </form>

        {history.length > 0 && (
          <div className="w-full max-w-2xl bg-gray-800 p-6 rounded-xl">
            <h3 className="text-2xl font-bold mb-4 border-b border-gray-700 pb-2">Recent Analysis</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="text-gray-400">
                    <th className="p-2">Code</th>
                    <th className="p-2">Score</th>
                    <th className="p-2">Date</th>
                    <th className="p-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.ticker} className="border-b border-gray-700 last:border-0 hover:bg-gray-700/50">
                      <td className="p-2 font-bold">{h.ticker}</td>
                      <td className={`p-2 font-bold ${h.score >= 80 ? 'text-green-400' : h.score >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>{h.score}</td>
                      <td className="p-2 text-sm text-gray-400">{new Date(h.date).toLocaleDateString()}</td>
                      <td className="p-2">
                        <button
                          onClick={() => router.push(`/analyze/${h.ticker}`)}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

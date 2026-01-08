export interface FinancialData {
    ticker: string;
    fiscal_years: string[];
    ordinary_income: number[];
    eps: number[];
    total_assets: number[];
    operating_cf: number[];
    cash_equivalents: number[];
    roe: number[];
    equity_ratio: number[];
    dividend_ps: number[];
    dividend_payout_ratio: number[];
}

export interface StockScore {
    ticker: string;
    total_score: number;
    breakdown: {
        ordinary_income: number;
        eps: number;
        total_assets: number;
        operating_cf: number;
        cash_equivalents: number;
        roe: number;
        equity_ratio: number;
        dividend: number;
        [key: string]: number;
    };
    financial_data: FinancialData;
}

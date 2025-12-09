import { useEffect, useRef } from "react";
import { createChart, IChartApi, ISeriesApi, Time } from "lightweight-charts";
import { useTranslation } from "react-i18next";

interface EquityCurveData {
  time: string;
  value: number;
}

interface MaxDrawdownInfo {
  peak_date: string;
  trough_date: string;
  peak_value: number;
  trough_value: number;
  drawdown_pct: number;
  drawdown_amount: number;
}

interface EquityCurveChartProps {
  data: EquityCurveData[];
  maxDrawdown?: MaxDrawdownInfo | null;
  height?: number;
}

export const EquityCurveChart = ({
  data,
  maxDrawdown,
  height = 400,
}: EquityCurveChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { color: "transparent" },
        textColor: "#d1d4dc",
      },
      grid: {
        vertLines: { color: "rgba(42, 46, 57, 0.5)" },
        horzLines: { color: "rgba(42, 46, 57, 0.5)" },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: "rgba(197, 203, 206, 0.4)",
      },
      timeScale: {
        borderColor: "rgba(197, 203, 206, 0.4)",
        timeVisible: true,
      },
    });

    chartRef.current = chart;

    // Add line series for equity curve
    const lineSeries = chart.addLineSeries({
      color: "#26a69a",
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 6,
      lastValueVisible: true,
      priceLineVisible: true,
    });

    // Format data for lightweight-charts
    const formattedData = data.map((d) => ({
      time: d.time.split("T")[0] as Time,
      value: d.value,
    }));

    lineSeries.setData(formattedData);

    // Add max drawdown markers if available
    if (maxDrawdown && maxDrawdown.peak_date && maxDrawdown.trough_date) {
      const markers = [
        {
          time: maxDrawdown.peak_date.split("T")[0] as Time,
          position: "aboveBar" as const,
          color: "#ef5350",
          shape: "circle" as const,
          text: "Peak",
          size: 1,
        },
        {
          time: maxDrawdown.trough_date.split("T")[0] as Time,
          position: "belowBar" as const,
          color: "#ef5350",
          shape: "circle" as const,
          text: "Trough",
          size: 1,
        },
      ];
      
      lineSeries.setMarkers(markers);
    }

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    // Cleanup
    return () => {
      window.removeEventListener("resize", handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [data, height]);

  return (
    <div
      ref={chartContainerRef}
      style={{
        width: "100%",
        height: `${height}px`,
        position: "relative",
      }}
    />
  );
};

import { useEffect, useRef } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  Time,
} from "lightweight-charts";
import { useTranslation } from "react-i18next";

interface EquityCurveData {
  time: string;
  value: number;
}

interface EquityCurveChartProps {
  data: EquityCurveData[];
  height?: number;
}

export const EquityCurveChart = ({
  data,
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

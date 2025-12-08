import { useEffect, useRef } from "react";
import { createChart, IChartApi, ISeriesApi, Time } from "lightweight-charts";
import { Box } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";

interface PriceData {
  time: string;
  value: number;
}

interface Signal {
  id: string;
  signal_time: string;
  symbol: string;
  status: string;
  price: number;
  signal_strength: number;
  message: string;
}

interface PriceChartProps {
  priceData: PriceData[];
  signals: Signal[];
  height?: number;
}

const PriceChart = ({ priceData, signals, height = 400 }: PriceChartProps) => {
  const { t } = useTranslation();
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { color: "#ffffff" },
        textColor: "#333",
      },
      grid: {
        vertLines: { color: "#e1e1e1" },
        horzLines: { color: "#e1e1e1" },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: "#cccccc",
      },
      timeScale: {
        borderColor: "#cccccc",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    const lineSeries = chart.addLineSeries({
      color: "#2962FF",
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 6,
      lastValueVisible: true,
      priceLineVisible: true,
    });

    seriesRef.current = lineSeries;

    // Set price data
    if (priceData.length > 0) {
      const formattedData = priceData.map((d) => ({
        time: d.time.split("T")[0] as Time,
        value: d.value,
      }));
      lineSeries.setData(formattedData);
    }

    // Add signal markers
    if (signals.length > 0) {
      const markers = signals.map((signal) => {
        const dateStr = signal.signal_time.split("T")[0].split(" ")[0];

        return {
          time: dateStr as Time,
          position:
            signal.status === "buy"
              ? ("belowBar" as const)
              : ("aboveBar" as const),
          color: signal.status === "buy" ? "#e91e63" : "#4caf50",
          shape:
            signal.status === "buy"
              ? ("arrowUp" as const)
              : ("arrowDown" as const),
          text: signal.status === "buy" ? "B" : "S",
          size: 1,
        };
      });
      lineSeries.setMarkers(markers);
    }

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [priceData, signals, height]);

  // Add hover tooltip
  useEffect(() => {
    if (!chartRef.current || !seriesRef.current) return;

    const chart = chartRef.current;
    const series = seriesRef.current;

    // Create tooltip element
    const toolTip = document.createElement("div");
    toolTip.style.cssText = `
      position: absolute;
      display: none;
      padding: 8px;
      box-sizing: border-box;
      font-size: 12px;
      text-align: left;
      z-index: 1000;
      top: 12px;
      left: 12px;
      pointer-events: none;
      border: 1px solid #2962FF;
      border-radius: 4px;
      background: white;
      color: #333;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    `;
    chartContainerRef.current?.appendChild(toolTip);

    // Subscribe to crosshair move
    chart.subscribeCrosshairMove((param) => {
      if (
        !param.time ||
        param.point === undefined ||
        param.point.x < 0 ||
        param.point.y < 0
      ) {
        toolTip.style.display = "none";
        return;
      }

      // Get price data
      const price = param.seriesData.get(series);
      if (!price) {
        toolTip.style.display = "none";
        return;
      }

      // Find corresponding signal
      const timeStr = param.time as string;
      const signal = signals.find((s) => {
        const signalDate = s.signal_time.split("T")[0].split(" ")[0];
        return signalDate === timeStr;
      });

      if (signal) {
        // Show signal details
        toolTip.style.display = "block";
        
        // Format signal time - convert UTC to local time
        const signalDate = new Date(signal.signal_time);
        const year = signalDate.getFullYear();
        const month = String(signalDate.getMonth() + 1).padStart(2, '0');
        const day = String(signalDate.getDate()).padStart(2, '0');
        const hours = String(signalDate.getHours()).padStart(2, '0');
        const minutes = String(signalDate.getMinutes()).padStart(2, '0');
        const signalTimeFormatted = `${year}-${month}-${day} ${hours}:${minutes}`;
        
        toolTip.innerHTML = `
          <div style="font-weight: bold; margin-bottom: 4px; color: ${
            signal.status === "buy" ? "#e91e63" : "#4caf50"
          }">
            ${signal.status === "buy" ? t("chart.buySignal") : t("chart.sellSignal")}
          </div>
          <div>${t("chart.time")}: ${signalTimeFormatted}</div>
          <div>${t("chart.price")}: ${signal.price.toFixed(2)}</div>
          <div>${t("chart.strength")}: ${signal.signal_strength.toFixed(3)}</div>
          <div style="margin-top: 4px; color: #666;">${signal.message}</div>
        `;

        // Position tooltip
        const coordinate = series.priceToCoordinate(signal.price);
        if (coordinate !== null) {
          toolTip.style.left = param.point.x + 15 + "px";
          toolTip.style.top = coordinate + "px";
        }
      } else {
        // Show only price
        toolTip.style.display = "block";
        toolTip.innerHTML = `
          <div>${t("chart.time")}: ${param.time}</div>
          <div>${t("chart.price")}: ${(price as any).value.toFixed(2)}</div>
        `;
        toolTip.style.left = param.point.x + 15 + "px";
        toolTip.style.top = param.point.y + "px";
      }
    });

    return () => {
      if (chartContainerRef.current?.contains(toolTip)) {
        chartContainerRef.current.removeChild(toolTip);
      }
    };
  }, [signals]);

  return (
    <Box
      ref={chartContainerRef}
      width="100%"
      height={`${height}px`}
      position="relative"
    />
  );
};

export default PriceChart;

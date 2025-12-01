import React, { useState, useEffect } from "react";
import { Box, Table, Text, Spinner, Button } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";
import { request } from "@/client/core/request";
import { OpenAPI } from "@/client";
import { Link } from "@tanstack/react-router";

interface BacktestItem {
  backtest_id: string;
  strategy_name: string;
  symbol: string;
  start_date: string;
  end_date: string;
  total_return_pct: number;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
  total_trades: number | null;
  win_rate: number | null;
  created_at: string;
}

interface BacktestListResponse {
  data: BacktestItem[];
  count: number;
}

function BacktestList() {
  const { t } = useTranslation();
  const [backtests, setBacktests] = useState<BacktestItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBacktests = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await request<BacktestListResponse>(OpenAPI, {
        method: "GET",
        url: "/api/v1/backtests/?page=1&size=20",
      });

      setBacktests(response.data || []);
    } catch (err: any) {
      console.error("获取回测数据失败:", err);
      setError("获取回测数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBacktests();
  }, []);

  if (loading) {
    return (
      <Box textAlign="center" py={8}>
        <Spinner size="lg" />
        <Text mt={4}>加载回测列表中...</Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Box textAlign="center" py={8}>
        <Text color="red.500">{error}</Text>
      </Box>
    );
  }

  return (
    <Box>
      <Table.Root variant="outline" size="sm">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="12%">
              {t("backtests.strategy")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="8%">
              {t("backtests.symbol")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="18%">
              {t("backtests.period")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="10%">
              {t("backtests.return")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="10%">
              {t("backtests.sharpe")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="10%">
              {t("backtests.drawdown")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="8%">
              {t("backtests.trades")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="10%">
              {t("backtests.winRate")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="14%">
              {t("backtests.createdAt")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="8%">
              {t("backtests.actions")}
            </Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {backtests.map((backtest) => (
            <Table.Row key={backtest.backtest_id}>
              <Table.Cell>
                <Text fontSize="sm" color="blue.600">
                  {backtest.strategy_name}
                </Text>
              </Table.Cell>
              <Table.Cell>{backtest.symbol}</Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">
                  {backtest.start_date} ~ {backtest.end_date}
                </Text>
              </Table.Cell>
              <Table.Cell>
                <Text
                  color={
                    backtest.total_return_pct >= 0 ? "red.500" : "green.500"
                  }
                  fontWeight="medium"
                >
                  {(backtest.total_return_pct * 100).toFixed(2)}%
                </Text>
              </Table.Cell>
              <Table.Cell>
                {backtest.sharpe_ratio !== null
                  ? backtest.sharpe_ratio.toFixed(2)
                  : "-"}
              </Table.Cell>
              <Table.Cell>
                {backtest.max_drawdown !== null
                  ? `${(backtest.max_drawdown * 100).toFixed(2)}%`
                  : "-"}
              </Table.Cell>
              <Table.Cell>{backtest.total_trades || "-"}</Table.Cell>
              <Table.Cell>
                {backtest.win_rate !== null
                  ? `${(backtest.win_rate * 100).toFixed(2)}%`
                  : "-"}
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">
                  {new Date(backtest.created_at).toLocaleString("zh-CN", {
                    year: "numeric",
                    month: "2-digit",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                    hour12: false,
                  })}
                </Text>
              </Table.Cell>

              <Table.Cell>
                <Link
                  to="/backtest/$id"
                  params={{ id: backtest.backtest_id }}
                  style={{
                    display: "inline-block",
                    padding: "4px 12px",
                    fontSize: "14px",
                    fontWeight: "500",
                    color: "white",
                    backgroundColor: "#3182ce",
                    borderRadius: "6px",
                    textDecoration: "none",
                    cursor: "pointer",
                  }}
                >
                  {t("backtests.view")}
                </Link>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Box>
  );
}

export default BacktestList;

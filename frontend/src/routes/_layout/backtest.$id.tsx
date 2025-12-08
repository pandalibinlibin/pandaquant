import {
  Container,
  Heading,
  Text,
  Box,
  Spinner,
  Grid,
  Table,
} from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { BacktestsService, StrategiesService } from "@/client";
import PriceChart from "@/components/Charts/PriceChart";

export const Route = createFileRoute("/_layout/backtest/$id")({
  component: BacktestDetail,
});

function BacktestDetail() {
  const { t } = useTranslation();
  const { id } = Route.useParams();

  const { data, isLoading, error } = useQuery({
    queryKey: ["backtest", id],
    queryFn: async () => {
      const response = await BacktestsService.getBacktestById({
        backtestId: id,
      });
      return response;
    },
  });

  const {
    data: signalsData,
    isLoading: signalsLoading,
    error: signalsError,
  } = useQuery({
    queryKey: ["signals", data?.strategy_name, id],
    enabled: !!data?.strategy_name,
    queryFn: async () => {
      if (!data?.strategy_name) return { data: [], total: 0 };
      const response = await StrategiesService.getBacktestSignals({
        strategyName: data.strategy_name,
        backtestId: id,
      });
      return response;
    },
  });

  const {
    data: priceData,
    isLoading: priceLoading,
    error: priceError,
  } = useQuery({
    queryKey: ["priceData", data?.strategy_name, id],
    enabled: !!data?.strategy_name,
    queryFn: async () => {
      if (!data?.strategy_name) return { data: [], total: 0 };
      const response = await StrategiesService.getBacktestPriceData({
        strategyName: data.strategy_name,
        backtestId: id,
      });
      return response;
    },
  });

  if (isLoading) {
    return (
      <Container maxW="full">
        <Box textAlign="center" py={8}>
          <Spinner size="lg" />
          <Text mt={4}>{t("common.loading")}</Text>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxW="full">
        <Box textAlign="center" py={8}>
          <Text color="red.500">{t("common.error")}</Text>
          <Text mt={2}>{error.message}</Text>
        </Box>
      </Container>
    );
  }

  const profitFactor =
    data?.avg_win && data?.avg_loss && data.avg_loss !== 0
      ? Math.abs(data.avg_win / data.avg_loss)
      : null;

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        {t("backtests.detail_title")}
      </Heading>

      {/* 基本信息 */}
      <Box mt={6} p={6} borderWidth="1px" borderRadius="lg">
        <Heading size="md" mb={4}>
          {t("backtests.basic_info")}
        </Heading>
        <Grid templateColumns="repeat(2, 1fr)" gap={4}>
          <Box>
            <Text fontWeight="bold">{t("backtests.strategy")}:</Text>
            <Text>{data?.strategy_name || "-"}</Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.symbol")}:</Text>
            <Text>{data?.symbol || "-"}</Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.start_date")}:</Text>
            <Text>{data?.start_date || "-"}</Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.end_date")}:</Text>
            <Text>{data?.end_date || "-"}</Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.initial_capital")}:</Text>
            <Text>
              {data?.initial_capital !== null &&
              data?.initial_capital !== undefined
                ? data.initial_capital.toFixed(2)
                : "-"}
            </Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.final_value")}:</Text>
            <Text>
              {data?.final_value !== null && data?.final_value !== undefined
                ? data.final_value.toFixed(2)
                : "-"}
            </Text>
          </Box>
        </Grid>
      </Box>

      {/* 收益指标 */}
      <Box mt={6} p={6} borderWidth="1px" borderRadius="lg">
        <Heading size="md" mb={4}>
          {t("backtests.performance_metrics")}
        </Heading>
        <Grid templateColumns="repeat(3, 1fr)" gap={4}>
          <Box>
            <Text fontWeight="bold">{t("backtests.total_return_abs")}:</Text>
            <Text color={data?.total_return >= 0 ? "red.500" : "green.500"}>
              {data?.total_return !== null && data?.total_return !== undefined
                ? data.total_return.toFixed(2)
                : "-"}
            </Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.return")}:</Text>
            <Text color={data?.total_return_pct >= 0 ? "red.500" : "green.500"}>
              {data?.total_return_pct !== null &&
              data?.total_return_pct !== undefined
                ? `${(data.total_return_pct * 100).toFixed(2)}%`
                : "-"}
            </Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.avg_annual_return")}:</Text>
            <Text>
              {data?.avg_annual_return !== null &&
              data?.avg_annual_return !== undefined
                ? `${(data.avg_annual_return * 100).toFixed(2)}%`
                : "-"}
            </Text>
          </Box>
        </Grid>
      </Box>

      {/* 风险指标 */}
      <Box mt={6} p={6} borderWidth="1px" borderRadius="lg">
        <Heading size="md" mb={4}>
          {t("backtests.risk_metrics")}
        </Heading>
        <Grid templateColumns="repeat(3, 1fr)" gap={4}>
          <Box>
            <Text fontWeight="bold">{t("backtests.drawdown")}:</Text>
            <Text>
              {data?.max_drawdown !== null && data?.max_drawdown !== undefined
                ? `${(data.max_drawdown * 100).toFixed(2)}%`
                : "-"}
            </Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.sharpe")}:</Text>
            <Text>
              {data?.sharpe_ratio !== null && data?.sharpe_ratio !== undefined
                ? data.sharpe_ratio.toFixed(2)
                : "-"}
            </Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.calmar_ratio")}:</Text>
            <Text>
              {data?.calmar_ratio !== null && data?.calmar_ratio !== undefined
                ? data.calmar_ratio.toFixed(2)
                : "-"}
            </Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.vwr")}:</Text>
            <Text>
              {data?.vwr !== null && data?.vwr !== undefined
                ? data.vwr.toFixed(2)
                : "-"}
            </Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.sqn")}:</Text>
            <Text>
              {data?.sqn !== null && data?.sqn !== undefined
                ? data.sqn.toFixed(2)
                : "-"}
            </Text>
          </Box>
        </Grid>
      </Box>

      {/* 交易统计 */}
      <Box mt={6} p={6} borderWidth="1px" borderRadius="lg">
        <Heading size="md" mb={4}>
          {t("backtests.trading_stats")}
        </Heading>
        <Grid templateColumns="repeat(3, 1fr)" gap={4}>
          <Box>
            <Text fontWeight="bold">{t("backtests.trades")}:</Text>
            <Text>{data?.total_trades || 0}</Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.winning_trades")}:</Text>
            <Text color="red.500">{data?.winning_trades || 0}</Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.losing_trades")}:</Text>
            <Text color="green.500">{data?.losing_trades || 0}</Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.winRate")}:</Text>
            <Text>
              {data?.win_rate !== null && data?.win_rate !== undefined
                ? `${(data.win_rate * 100).toFixed(2)}%`
                : "-"}
            </Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.avg_win")}:</Text>
            <Text>
              {data?.avg_win !== null && data?.avg_win !== undefined
                ? data.avg_win.toFixed(2)
                : "-"}
            </Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.avg_loss")}:</Text>
            <Text>
              {data?.avg_loss !== null && data?.avg_loss !== undefined
                ? data.avg_loss.toFixed(2)
                : "-"}
            </Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.profit_factor")}:</Text>
            <Text>{profitFactor !== null ? profitFactor.toFixed(2) : "-"}</Text>
          </Box>
          <Box>
            <Text fontWeight="bold">{t("backtests.createdAt")}:</Text>
            <Text fontSize="sm">
              {data?.created_at
                ? new Date(data.created_at).toLocaleString("zh-CN", {
                    year: "numeric",
                    month: "2-digit",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                    hour12: false,
                  })
                : "-"}
            </Text>
          </Box>
        </Grid>
      </Box>
      {/* 价格图表 */}
      <Box mt={6} p={6} borderWidth="1px" borderRadius="lg">
        <Heading size="md" mb={4}>
          {t("backtests.price_chart_title")}
        </Heading>
        {priceLoading ? (
          <Box display="flex" justifyContent="center" py={8}>
            <Spinner size="lg" />
          </Box>
        ) : priceError ? (
          <Text color="red.500">
            {t("common.error")}: {priceError.message}
          </Text>
        ) : (
          <PriceChart
            priceData={priceData?.data || []}
            signals={signalsData?.data || []}
            height={400}
          />
        )}
      </Box>

      {/* 交易信号列表 */}
      {signalsData?.data && signalsData.data.length > 0 && (
        <Box mt={6} p={6} borderWidth="1px" borderRadius="lg">
          <Heading size="md" mb={4}>
            {t("backtests.signals_title")}
          </Heading>
          <Table.Root variant="outline" size="sm">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader w="15%">
                  {t("signals.time")}
                </Table.ColumnHeader>
                <Table.ColumnHeader w="10%">
                  {t("signals.symbol")}
                </Table.ColumnHeader>
                <Table.ColumnHeader w="10%">
                  {t("signals.action")}
                </Table.ColumnHeader>
                <Table.ColumnHeader w="12%">
                  {t("signals.price")}
                </Table.ColumnHeader>
                <Table.ColumnHeader w="12%">
                  {t("signals.strength")}
                </Table.ColumnHeader>
                <Table.ColumnHeader w="41%">
                  {t("signals.message")}
                </Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {signalsData.data.map((signal: any) => (
                <Table.Row key={signal.id}>
                  <Table.Cell w="15%">
                    <Text fontSize="sm">
                      {signal.signal_time
                        ? new Date(signal.signal_time).toLocaleString("zh-CN", {
                            month: "2-digit",
                            day: "2-digit",
                            hour: "2-digit",
                            minute: "2-digit",
                            hour12: false,
                          })
                        : "-"}
                    </Text>
                  </Table.Cell>
                  <Table.Cell w="10%">
                    <Text color="blue.600" fontWeight="medium">
                      {signal.symbol}
                    </Text>
                  </Table.Cell>
                  <Table.Cell w="10%">
                    <Text
                      color={signal.status === "buy" ? "red.500" : "green.500"}
                      fontWeight="bold"
                    >
                      {signal.status === "buy" ? "买入" : "卖出"}
                    </Text>
                  </Table.Cell>
                  <Table.Cell w="12%">
                    {signal.price ? signal.price.toFixed(2) : "-"}
                  </Table.Cell>
                  <Table.Cell w="12%">
                    {signal.signal_strength
                      ? signal.signal_strength.toFixed(3)
                      : "-"}
                  </Table.Cell>
                  <Table.Cell w="41%">
                    <Text fontSize="sm" color="gray.600">
                      {signal.message || "-"}
                    </Text>
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
        </Box>
      )}
    </Container>
  );
}

import React, { useState, useEffect } from "react";
import {
  Box,
  Heading,
  Button,
  Input,
  NativeSelectRoot,
  NativeSelectField,
  Stack,
  Grid,
  Spinner,
  Text,
} from "@chakra-ui/react";
import { Field } from "@/components/ui/field";
import { useTranslation } from "react-i18next";
import { useSearch } from "@tanstack/react-router";
import { catchErrorCodes, request } from "@/client/core/request";
import { OpenAPI } from "@/client";

interface Strategy {
  name: string;
  description: string | null;
}

interface StrategiesResponse {
  data: Strategy[];
  count: number;
}

const BacktestForm = () => {
  const { t } = useTranslation();
  const search = useSearch({ from: "/_layout/backtests" });

  // 表单状态
  const [strategyName, setStrategyName] = useState(search?.strategy || "");
  const [symbol, setSymbol] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [initialCapital, setInitialCapital] = useState(100000);

  // 策略列表状态
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loadingStrategies, setLoadingStrategies] = useState(true);
  const [errorStrategies, setErrorStrategies] = useState<string | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [backtestId, setBacktestId] = useState<string | null>(null);
  const [pollingCount, setPollingCount] = useState(0);

  // 获取策略列表
  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      setLoadingStrategies(true);
      setErrorStrategies(null);

      const response = await request<StrategiesResponse>(OpenAPI, {
        method: "GET",
        url: "/api/v1/strategies",
      });

      setStrategies(response.data || []);
    } catch (err: any) {
      console.error("获取策略列表失败:", err);
      setErrorStrategies("获取策略列表失败");
    } finally {
      setLoadingStrategies(false);
    }
  };

  const handleSubmit = async () => {
    if (!strategyName) {
      setSubmitError("请选择策略");
      return;
    }

    if (!symbol) {
      setSubmitError("请输入股票代码");
      return;
    }

    if (!startDate || !endDate) {
      setSubmitError("请选择日期范围");
      return;
    }

    try {
      setSubmitting(true);
      setSubmitError(null);
      setSubmitSuccess(false);

      const response = await request<{ backtest_id: string }>(OpenAPI, {
        method: "POST",
        url: `/api/v1/strategies/${strategyName}/backtest`,
        body: {
          symbol,
          start_date: startDate,
          end_date: endDate,
          initial_capital: initialCapital,
        },
      });

      setBacktestId(response.backtest_id);
      setSubmitSuccess(true);
      setPollingCount(0);

      setStrategyName("");
      setSymbol("");
      setStartDate("");
      setEndDate("");
      setInitialCapital(100000);
    } catch (err: any) {
      console.error("提交回测失败:", err);
      setSubmitError(err.message || "提交失败, 请重试");
    } finally {
      setSubmitting(false);
    }
  };

  // 轮询检查回测状态
  const checkBacktestStatus = async (id: string) => {
    try {
      const response = await request<{ status: string }>(OpenAPI, {
        method: "GET",
        url: `/api/v1/backtests/${id}`,
      });

      if (response.status === "completed") {
        // 回测完成，刷新页面
        window.location.reload();
      } else if (pollingCount < 20) {
        // 继续轮询
        setPollingCount(pollingCount + 1);
      }
    } catch (err: any) {
      console.error("查询回测状态失败:", err);
    }
  };

  // 当有回测 ID 时，开始轮询
  useEffect(() => {
    if (backtestId && pollingCount < 20) {
      const timer = setTimeout(() => {
        checkBacktestStatus(backtestId);
      }, 5000); // 每 5 秒查询一次

      return () => clearTimeout(timer);
    }
  }, [backtestId, pollingCount]);

  return (
    <Box>
      <Heading size="md" mb={4}>
        {t("backtests.create_title")}
      </Heading>

      <Grid
        templateColumns={{ base: "1fr", md: "1fr 1fr" }}
        gap={4}
        maxW="800px"
      >
        {/* 策略选择 */}
        <Field label={t("backtests.select_strategy")}>
          {loadingStrategies ? (
            <Box py={2}>
              <Spinner size="sm" /> 加载策略列表...
            </Box>
          ) : errorStrategies ? (
            <Box py={2} color="red.500">
              ⚠️ {errorStrategies}
            </Box>
          ) : (
            <NativeSelectRoot>
              <NativeSelectField
                placeholder={t("backtests.select_strategy_placeholder")}
                value={strategyName}
                onChange={(e) => setStrategyName(e.target.value)}
              >
                {strategies.map((strategy) => (
                  <option key={strategy.name} value={strategy.name}>
                    {strategy.name}
                  </option>
                ))}
              </NativeSelectField>
            </NativeSelectRoot>
          )}
        </Field>

        {/* 股票代码 */}
        <Field label={t("backtests.input_symbol")}>
          <Input
            placeholder={t("backtests.input_symbol_placeholder")}
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          />
        </Field>

        {/* 开始日期 */}
        <Field label={t("backtests.start_date")}>
          <Input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </Field>

        {/* 结束日期 */}
        <Field label={t("backtests.end_date")}>
          <Input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </Field>

        {/* 初始资金 */}
        <Field label={t("backtests.initial_capital")}>
          <Input
            type="number"
            value={initialCapital}
            onChange={(e) => setInitialCapital(Number(e.target.value))}
          />
        </Field>

        {/* 错误提示 */}
        {submitError && (
          <Box gridColumn={{ base: "1", md: "1 / -1" }}>
            <Box py={2} px={4} bg="red.50" color="red.600" borderRadius="md">
              ⚠️ {submitError}
            </Box>
          </Box>
        )}

        {/* 成功提示 */}
        {submitSuccess && (
          <Box gridColumn={{ base: "1", md: "1 / -1" }}>
            <Box
              py={3}
              px={4}
              bg="green.50"
              color="green.600"
              borderRadius="md"
              borderLeft="4px solid"
              borderColor="green.500"
            >
              <Box display="flex" alignItems="center" gap={3}>
                <Spinner size="sm" color="green.500" />
                <Box flex="1">
                  <Text fontWeight="semibold" mb={1}>
                    ✅ 回测已提交成功！
                  </Text>
                  <Text fontSize="sm" color="green.600">
                    正在后台运行回测，预计需要几秒到几分钟...
                  </Text>
                  <Text fontSize="xs" color="green.500" mt={1}>
                    已检查 {pollingCount} 次 / 最多 20 次 · 每 5 秒检查一次 ·
                    完成后自动刷新
                  </Text>
                </Box>
              </Box>
            </Box>
          </Box>
        )}

        {/* 提交按钮 */}
        <Box gridColumn={{ base: "1", md: "1 / -1" }}>
          <Button
            colorScheme="blue"
            size="lg"
            width="full"
            onClick={handleSubmit}
            loading={submitting}
            disabled={submitting}
          >
            {submitting ? t("backtests.submitting") : t("backtests.submit")}
          </Button>
        </Box>
      </Grid>
    </Box>
  );
};

export default BacktestForm;

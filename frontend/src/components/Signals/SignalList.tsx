import React, { useState, useEffect } from "react";
import { Box, Table, Text, Spinner, Button } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";
import { request } from "@/client/core/request";
import { OpenAPI } from "@/client";

interface SignalInfo {
  id: string;
  symbol: string;
  action: string;
  confidence: number;
  timestamp: string;
  metadata: Record<string, any>;
  strategy_name?: string;
}

interface SignalListResponse {
  signal: SignalInfo[];
  total: number;
  page: number;
  size: number;
}

const SignalList = () => {
  const { t } = useTranslation();
  const [signals, setSignals] = useState<SignalInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getActionColor = (action: string) => {
    switch (action.toLowerCase()) {
      case "buy":
        return "red.500";
      case "sell":
        return "green.500";
      default:
        return "gray.500";
    }
  };

  // 置信度统一使用黑色，不再按数值区分颜色

  const fetchSignals = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await request<SignalListResponse>(OpenAPI, {
        method: "GET",
        url: "/api/v1/signals/?page=1&size=20",
      });

      setSignals(response.signal || []);
    } catch (err: any) {
      console.error("获取信号数据失败:", err);
      setError("获取信号数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, []);

  if (loading) {
    return (
      <Box textAlign="center" py={8}>
        <Spinner size="lg" />
        <Text mt={4}>加载信号列表中...</Text>
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
              {t("signals.symbol")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="15%">策略</Table.ColumnHeader>
            <Table.ColumnHeader w="10%">
              {t("signals.action")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="10%">
              {t("signals.confidence")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="10%">价格</Table.ColumnHeader>
            <Table.ColumnHeader w="25%">
              {t("signals.timestamp")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="18%">操作</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {signals.map((signal) => (
            <Table.Row key={signal.id}>
              <Table.Cell w="12%">{signal.symbol}</Table.Cell>
              <Table.Cell w="15%">
                <Text fontSize="sm" color="blue.600">
                  {signal.strategy_name || "-"}
                </Text>
              </Table.Cell>
              <Table.Cell w="10%">
                <Text color={getActionColor(signal.action)} fontWeight="medium">
                  {signal.action}
                </Text>
              </Table.Cell>
              <Table.Cell w="10%">
                {(signal.confidence * 100).toFixed(1)}%
              </Table.Cell>
              <Table.Cell w="10%">
                {signal.metadata?.price ? signal.metadata.price.toFixed(2) : "-"}
              </Table.Cell>
              <Table.Cell w="25%">
                {new Date(signal.timestamp).toLocaleString("zh-CN", {
                  year: "numeric",
                  month: "2-digit",
                  day: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                  hour12: false,
                })}
              </Table.Cell>
              <Table.Cell w="20%">
                <Box display="flex" gap={2}>
                  <Button size="sm" colorScheme="blue">
                    查看
                  </Button>
                </Box>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>

      {signals.length === 0 && (
        <Box textAlign="center" py={8}>
          <Text color="gray.500">暂无信号数据</Text>
        </Box>
      )}
    </Box>
  );
};

export default SignalList;

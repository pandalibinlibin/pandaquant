import React, { useState, useEffect } from "react";
import { Box, Table, Button, Text, Spinner, Alert } from "@chakra-ui/react";
import { MdError } from "react-icons/md";

import { useTranslation } from "react-i18next";
import { request } from "@/client/core/request";
import { OpenAPI } from "@/client";

interface Strategy {
  name: string;
  description: string | null;
}

interface StrategiesResponse {
  data: Strategy[];
  count: number;
}

const StrategyList = () => {
  const { t } = useTranslation();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await request<StrategiesResponse>(OpenAPI, {
        method: "GET",
        url: "/api/v1/strategies",
      });

      setStrategies(response.data || []);
    } catch (err: any) {
      console.error("获取策略数据失败:", err);
      setError("获取策略数据失败");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box textAlign="center" py={8}>
        <Spinner size="lg" />
        <Text mt={4}>加载策略列表中...</Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert status="error">
        <MdError />
        错误: {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Table.Root size={{ base: "sm", md: "md" }} variant="outline">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="30%">
              {t("strategies.name")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="45%">
              {t("strategies.description")}
            </Table.ColumnHeader>
            <Table.ColumnHeader w="25%">操作</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {strategies.map((strategy) => (
            <Table.Row key={strategy.name}>
              <Table.Cell fontWeight="medium" color="blue.600" w="30%">
                {strategy.name}
              </Table.Cell>
              <Table.Cell color="gray.600" w="45%">
                {strategy.description || "暂无描述"}
              </Table.Cell>
              <Table.Cell w="25%">
                <Box display="flex" gap={2} flexWrap="wrap">
                  <Button size="sm" colorScheme="blue">
                    {t("strategies.backtest")}
                  </Button>
                  <Button size="sm" variant="outline">
                    查看详情
                  </Button>
                </Box>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>

      {strategies.length === 0 && (
        <Box textAlign="center" py={8}>
          <Text color="gray.500">暂无策略数据</Text>
        </Box>
      )}
    </Box>
  );
};

export default StrategyList;

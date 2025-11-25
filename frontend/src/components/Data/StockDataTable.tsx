import { Box, Spinner, Text, Table } from "@chakra-ui/react";

import { useTranslation } from "react-i18next";

interface StockDataTableProps {
  data: any[];
  loading: boolean;
  error: string | null;
}

function StockDataTable({ data, loading, error }: StockDataTableProps) {
  const { t } = useTranslation();
  if (loading) {
    return (
      <Box textAlign="center" py={8}>
        <Spinner size="lg" color="blue.500" />
        <Text mt={4} color="gray.600">
          {t("data.loading")}
        </Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Box textAlign="center" py={8}>
        <Text color="red.500" fontSize="lg">
          {t("common.error")}: {error}
        </Text>
      </Box>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Box textAlign="center" py={8}>
        <Text color="gray.500" fontSize="lg">
          {t("data.noData")}
        </Text>
      </Box>
    );
  }

  return (
    <Box>
      {/* 数据统计 */}
      <Box mb={4}>
        <Text fontSize="sm" color="gray.600">
          共{" "}
          <Text as="span" fontWeight="bold">
            {data.length}
          </Text>{" "}
          条记录
        </Text>
      </Box>

      {/* 股票数据表格 */}
      <Box overflowX="auto" borderWidth={1} borderRadius="md">
        <Table.Root size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>{t("data.symbol")}</Table.ColumnHeader>
              <Table.ColumnHeader>{t("data.date")}</Table.ColumnHeader>
              <Table.ColumnHeader>{t("data.open")}</Table.ColumnHeader>
              <Table.ColumnHeader>{t("data.close")}</Table.ColumnHeader>
              <Table.ColumnHeader>{t("data.high")}</Table.ColumnHeader>
              <Table.ColumnHeader>{t("data.low")}</Table.ColumnHeader>
              <Table.ColumnHeader>{t("data.change")}</Table.ColumnHeader>
              <Table.ColumnHeader>{t("data.pctChange")}</Table.ColumnHeader>
              <Table.ColumnHeader>{t("data.volume")}</Table.ColumnHeader>
              <Table.ColumnHeader>{t("data.amount")}</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {data.map((row, index) => (
              <Table.Row key={index} _hover={{ bg: "gray.50" }}>
                <Table.Cell fontWeight="medium" color="blue.600">
                  {row.symbol || row.ts_code || "-"}
                </Table.Cell>
                <Table.Cell fontWeight="medium">
                  {row.timestamp.split("T")[0].replace(/-/g, "/")}
                </Table.Cell>
                <Table.Cell>{row.open?.toFixed(2) || "-"}</Table.Cell>
                <Table.Cell fontWeight="medium">
                  {row.close?.toFixed(2) || "-"}
                </Table.Cell>
                <Table.Cell color="red.500">
                  {row.high?.toFixed(2) || "-"}
                </Table.Cell>
                <Table.Cell color="green.500">
                  {row.low?.toFixed(2) || "-"}
                </Table.Cell>
                <Table.Cell
                  color={
                    row.change > 0
                      ? "red.500"
                      : row.change < 0
                        ? "green.500"
                        : "gray.500"
                  }
                >
                  {row.change?.toFixed(2) || "-"}
                </Table.Cell>
                <Table.Cell
                  fontWeight="bold"
                  color={
                    row.pct_chg > 0
                      ? "red.500"
                      : row.pct_chg < 0
                        ? "green.500"
                        : "gray.500"
                  }
                >
                  {row.pct_chg
                    ? `${row.pct_chg > 0 ? "+" : ""}${row.pct_chg.toFixed(2)}%`
                    : "-"}
                </Table.Cell>
                <Table.Cell>
                  {row.vol ? (row.vol / 10000).toFixed(2) + "万手" : "-"}
                </Table.Cell>
                <Table.Cell>
                  {row.amount ? (row.amount / 10000).toFixed(2) + "万元" : "-"}
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    </Box>
  );
}

export default StockDataTable;

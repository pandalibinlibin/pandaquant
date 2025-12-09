import { Box, Table, Text } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";

interface MonthlyData {
  year: number;
  months: {
    [key: number]: number | null;
  };
  annual: number;
}

interface MonthlyReturnsTableProps {
  data: MonthlyData[];
}

export const MonthlyReturnsTable = ({ data }: MonthlyReturnsTableProps) => {
  const { t } = useTranslation();

  // Month names
  const monthNames = [
    t("common.months.jan"),
    t("common.months.feb"),
    t("common.months.mar"),
    t("common.months.apr"),
    t("common.months.may"),
    t("common.months.jun"),
    t("common.months.jul"),
    t("common.months.aug"),
    t("common.months.sep"),
    t("common.months.oct"),
    t("common.months.nov"),
    t("common.months.dec"),
  ];

  // Get cell background color based on return value
  const getCellColor = (value: number | null) => {
    if (value === null || value === 0) return "gray.50";
    return value > 0 ? "green.50" : "red.50";
  };

  // Get text color based on return value
  const getTextColor = (value: number | null) => {
    if (value === null || value === 0) return "gray.500";
    return value > 0 ? "green.700" : "red.700";
  };

  // Format return value
  const formatReturn = (value: number | null) => {
    if (value === null) return "-";
    if (value === 0) return "0.00%";
    return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  return (
    <Box overflowX="auto">
      <Table.Root size="sm" variant="outline">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader textAlign="center" fontWeight="bold">
              {t("backtests.year")}
            </Table.ColumnHeader>
            {monthNames.map((month, index) => (
              <Table.ColumnHeader key={index} textAlign="center" fontWeight="bold">
                {month}
              </Table.ColumnHeader>
            ))}
            <Table.ColumnHeader textAlign="center" fontWeight="bold">
              {t("backtests.annual")}
            </Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {data.map((yearData) => (
            <Table.Row key={yearData.year}>
              <Table.Cell textAlign="center" fontWeight="semibold">
                {yearData.year}
              </Table.Cell>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((month) => {
                const value = yearData.months[month];
                return (
                  <Table.Cell
                    key={month}
                    textAlign="center"
                    bg={getCellColor(value)}
                  >
                    <Text
                      fontSize="sm"
                      color={getTextColor(value)}
                      fontWeight="medium"
                    >
                      {formatReturn(value)}
                    </Text>
                  </Table.Cell>
                );
              })}
              <Table.Cell
                textAlign="center"
                bg={getCellColor(yearData.annual)}
                fontWeight="bold"
              >
                <Text
                  fontSize="sm"
                  color={getTextColor(yearData.annual)}
                  fontWeight="bold"
                >
                  {formatReturn(yearData.annual)}
                </Text>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Box>
  );
};

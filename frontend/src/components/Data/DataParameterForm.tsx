import { Box, Heading, Text, Input, HStack, Button } from "@chakra-ui/react";
import { Field } from "@/components/ui/field";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import { OpenAPI } from "@/client/core/OpenAPI";
import { request } from "@/client/core/request";
import StockDataTable from "./StockDataTable";

interface DataParameterFormProps {
  dataType: string;
}

function DataParameterForm({ dataType }: DataParameterFormProps) {
  const { t } = useTranslation();
  const [stockDailyParams, setStockDailyParams] = useState({
    symbol: "",
    start_date: "",
    end_date: "",
  });
  const [loading, setLoading] = useState(false);
  const [responseData, setResponseData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      console.log("提交参数:", stockDailyParams);

      const response = await request(OpenAPI, {
        method: "POST",
        url: "/api/v1/data/stock",
        body: {
          data_type: "daily",
          symbol: stockDailyParams.symbol,
          start_date: stockDailyParams.start_date,
          end_date: stockDailyParams.end_date,
        },
      });

      console.log("API 响应:", response);
      setResponseData(response);
      setError(null);
    } catch (error) {
      console.error("查询失败:", error);
      setError("数据获取失败，请稍后重试");
      setResponseData(null);
    } finally {
      setLoading(false);
    }
  };

  const renderStockDailyForm = () => (
    <Box>
      <Field mb={4} label={t("data.stockSymbol")}>
        <Input
          value={stockDailyParams.symbol}
          onChange={(e) =>
            setStockDailyParams({
              ...stockDailyParams,
              symbol: e.target.value,
            })
          }
          placeholder="000001.SZ"
        />
      </Field>

      <HStack gap={4} mb={4}>
        <Field mb={4} label={t("data.startDate")}>
          <Input
            type="date"
            value={stockDailyParams.start_date}
            onChange={(e) =>
              setStockDailyParams({
                ...stockDailyParams,
                start_date: e.target.value,
              })
            }
          />
        </Field>

        <Field mb={4} label={t("data.endDate")}>
          <Input
            type="date"
            value={stockDailyParams.end_date}
            onChange={(e) =>
              setStockDailyParams({
                ...stockDailyParams,
                end_date: e.target.value,
              })
            }
          />
        </Field>
      </HStack>
      <Button colorScheme="blue" onClick={handleSubmit} loading={loading}>
        {t("common.search")}
      </Button>
    </Box>
  );

  return (
    <Box p={4} borderWidth={1} borderRadius="md" mb={4}>
      <Heading size="md" mb={4}>
        {t("data.parameters")}
      </Heading>

      {dataType === "stock_daily" ? (
        renderStockDailyForm()
      ) : (
        <Text>
          {t("data.currentSelection")}
          {dataType}
        </Text>
      )}

      {error && (
        <Box
          mt={4}
          p={4}
          bg="red.50"
          borderRadius="md"
          borderWidth={1}
          borderColor="red.200"
        >
          <Text color="red.600">{error}</Text>
        </Box>
      )}

      {responseData && (
        <Box>
          <StockDataTable
            data={responseData.data}
            loading={false}
            error={null}
          />
        </Box>
      )}
    </Box>
  );
}

export default DataParameterForm;

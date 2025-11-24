import { Box, Heading, Stack, Text } from "@chakra-ui/react";
import { Radio, RadioGroup } from "@/components/ui/radio";
import { useTranslation } from "react-i18next";

interface DataTypeSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

function DataTypeSelector({ value, onChange }: DataTypeSelectorProps) {
  const { t } = useTranslation();
  return (
    <Box p={4} borderWidth={1} borderRadius="md" mb={4}>
      <Heading size="md" mb={3}>
        {t("data.dataType")}
      </Heading>
      <RadioGroup value={value} onValueChange={(details) => details.value && onChange(details.value)}>
        <Stack direction="column">
          <Box>
            <Radio value="stock_daily">{t("data.stockDaily")}</Radio>
            <Text fontSize="sm" color="gray.600" ml={6}>
              {t("data.stockDailyDesc")}
            </Text>
          </Box>
          <Box>
            <Radio value="stock_minute">{t("data.stockMinute")}</Radio>
            <Text fontSize="sm" color="gray.600" ml={6}>
              {t("data.stockMinuteDesc")}
            </Text>
          </Box>
          <Box>
            <Radio value="stock_financial">{t("data.stockFinancial")}</Radio>
            <Text fontSize="sm" color="gray.600" ml={6}>
              {t("data.stockFinancialDesc")}
            </Text>
          </Box>
          <Box>
            <Radio value="macro">{t("data.macroData")}</Radio>
            <Text fontSize="sm" color="gray.600" ml={6}>
              {t("data.macroDataDesc")}
            </Text>
          </Box>
          <Box>
            <Radio value="industry">{t("data.industryData")}</Radio>
            <Text fontSize="sm" color="gray.600" ml={6}>
              {t("data.industryDataDesc")}
            </Text>
          </Box>
        </Stack>
      </RadioGroup>
    </Box>
  );
}

export default DataTypeSelector;

import { Container, Heading, VStack } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import DataTypeSelector from "@/components/Data/DataTypeSelector";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import DataParameterForm from "@/components/Data/DataParameterForm";

export const Route = createFileRoute("/_layout/data")({
  component: Data,
});

function Data() {
  const { t } = useTranslation();
  const [dataType, setDataType] = useState("stock_daily");

  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        {t("data.title")}
      </Heading>

      <VStack gap={4} align="stretch" mt={6}>
        <DataTypeSelector value={dataType} onChange={setDataType} />
        <DataParameterForm dataType={dataType} />
      </VStack>
    </Container>
  );
}

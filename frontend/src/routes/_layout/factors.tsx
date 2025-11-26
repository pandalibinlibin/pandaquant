import { Container, Heading, VStack } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import FactorList from "@/components/Factors/FactorList";

export const Route = createFileRoute("/_layout/factors")({
  component: Factors,
});

function Factors() {
  const { t } = useTranslation();
  const [factorType, setFactorType] = useState("technical");

  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        {t("factors.title")}
      </Heading>

      <VStack gap={4} align="stretch" mt={6}>
        <FactorList factorType={factorType} />
      </VStack>
    </Container>
  );
}

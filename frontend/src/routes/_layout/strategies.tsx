import { Container, Heading, VStack } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import StrategyList from "@/components/Strategies/StrategyList";

export const Route = createFileRoute("/_layout/strategies")({
  component: Strategies,
});

function Strategies() {
  const { t } = useTranslation();

  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        {t("strategies.title")}
      </Heading>

      <VStack gap={4} align="stretch" mt={6}>
        <StrategyList />
      </VStack>
    </Container>
  );
}

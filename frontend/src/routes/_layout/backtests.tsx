import { Container, Heading } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import BacktestList from "@/components/Backtests/BacktestList";

export const Route = createFileRoute("/_layout/backtests")({
  component: Backtests,
});

function Backtests() {
  const { t } = useTranslation();

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        {t("backtests.title")}
      </Heading>
      <BacktestList />
    </Container>
  );
}

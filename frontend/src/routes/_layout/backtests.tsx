import { Container, Heading, Box } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import BacktestList from "@/components/Backtests/BacktestList";
import BacktestForm from "@/components/Backtests/BacktestForm";

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
      <Box mt={8} mb={8}>
        <BacktestForm />
      </Box>

      <BacktestList />
    </Container>
  );
}

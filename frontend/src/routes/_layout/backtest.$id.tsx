import { Container, Heading, Text } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute("/_layout/backtest/$id")({
  component: BacktestDetail,
});

function BacktestDetail() {
  const { t } = useTranslation();
  const { id } = Route.useParams();

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        {t("backtests.detail_title")}
      </Heading>
      <Text mt={4}>回测 ID: {id}</Text>
    </Container>
  );
}

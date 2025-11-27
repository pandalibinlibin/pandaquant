import { createFileRoute } from "@tanstack/react-router";
import { Container, Heading } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";
import SignalList from "@/components/Signals/SignalList";

export const Route = createFileRoute("/_layout/signals")({
  component: RouteComponent,
});

function RouteComponent() {
  const { t } = useTranslation();

  return (
    <Container maxW="7xl" py={6}>
      <Heading size="lg" mb={6}>
        {t("signals.title")}
      </Heading>
      <SignalList />
    </Container>
  );
}

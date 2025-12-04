import {
  Container,
  Heading,
  VStack,
  Text,
  Spinner,
  Box,
  Table,
} from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { request } from "@/client/core/request";
import { OpenAPI } from "@/client";

export const Route = createFileRoute("/_layout/strategy/$name")({
  component: StrategyDetail,
});

function StrategyDetail() {
  const { t } = useTranslation();
  const { name } = Route.useParams();

  const { data, isLoading, error } = useQuery({
    queryKey: ["strategy-detail", name],
    queryFn: async () => {
      const response = await request(OpenAPI, {
        method: "GET",
        url: `/api/v1/strategies/${name}/detail`,
      });
      return response;
    },
  });

  if (isLoading) {
    return (
      <Container maxW="full">
        <Box textAlign="center" py={8}>
          <Spinner size="lg" />
          <Text mt={4}>{t("common.loading")}</Text>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxW="full">
        <Box textAlign="center" py={8}>
          <Text color="red.500">{t("common.error")}</Text>
          <Text mt={2}>{error.message}</Text>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        {data.name}
      </Heading>

      {/* 策略描述 */}
      <Box mt={4} p={4} borderWidth="1px" borderRadius="lg">
        <Text fontWeight="bold" mb={2}>
          {t("strategies.description")}:
        </Text>
        <Text color="gray.600">{data.description || "-"}</Text>
      </Box>

      {/* DataGroup 列表 */}
      <Box mt={6}>
        <Heading size="md" mb={4}>
          DataGroup {t("common.configuration")}
        </Heading>

        {data.data_groups?.map((group: any, index: number) => (
          <Box key={index} mt={4} p={4} borderWidth="1px" borderRadius="lg">
            <Text fontWeight="bold" fontSize="lg" mb={3}>
              {group.name} ({group.datagroup_class})
            </Text>

            <VStack align="stretch" gap={2} mb={4}>
              <Text fontSize="sm">
                <Text as="span" fontWeight="bold">
                  {t("strategies.dataType")}:
                </Text>{" "}
                {group.data_type}
              </Text>
              <Text fontSize="sm">
                <Text as="span" fontWeight="bold">
                  {t("strategies.weight")}:
                </Text>{" "}
                {group.weight}
              </Text>
            </VStack>

            {/* 因子实例表格 */}
            <Text fontWeight="bold" mb={2}>
              {t("factors.title")}:
            </Text>
            <Table.Root size="sm" variant="outline">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>
                    {t("factors.instanceName")}
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>
                    {t("factors.className")}
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>
                    {t("factors.parameters")}
                  </Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {group.factors?.map((factor: any, fIndex: number) => (
                  <Table.Row key={fIndex}>
                    <Table.Cell fontWeight="medium" color="blue.600">
                      {factor.instance_name}
                    </Table.Cell>
                    <Table.Cell color="purple.600">
                      {factor.factor_class}
                    </Table.Cell>
                    <Table.Cell>
                      <Text fontSize="xs" color="gray.600">
                        {JSON.stringify(factor.parameters)}
                      </Text>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          </Box>
        ))}
      </Box>
    </Container>
  );
}

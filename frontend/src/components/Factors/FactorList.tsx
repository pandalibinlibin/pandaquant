import { Box, Text, Spinner, Table } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";
import { useState, useEffect } from "react";
import { request } from "@/client/core/request";
import { OpenAPI } from "@/client";

interface FactorListProps {
  factorType?: string;
}

function FactorList({ factorType }: FactorListProps) {
  const { t } = useTranslation();
  const [factors, setFactors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFactors = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await request(OpenAPI, {
        method: "GET",
        url: "/api/v1/factors/",
      });

      setFactors(response || []);
    } catch (err: any) {
      console.error("获取因子数据失败:", err);
      setError("获取因子数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFactors();
  }, []);

  if (loading) {
    return (
      <Box textAlign="center" py={8}>
        <Spinner size="lg" color="blue.500" />
        <Text mt={4} color="gray.600">
          {t("factors.loading")}
        </Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Box textAlign="center" py={8}>
        <Text color="red.500" fontSize="lg">
          {t("common.error")}: {error}
        </Text>
      </Box>
    );
  }

  return (
    <Box>
      <Text color="gray.500" fontSize="sm" mb={4}>
        共 {factors.length} 个因子
      </Text>

      <Table.Root size="sm" variant="outline">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>{t("factors.factorName")}</Table.ColumnHeader>
            <Table.ColumnHeader>{t("factors.category")}</Table.ColumnHeader>
            <Table.ColumnHeader>{t("factors.factorClass")}</Table.ColumnHeader>
            <Table.ColumnHeader>{t("factors.description")}</Table.ColumnHeader>
            <Table.ColumnHeader>{t("factors.parameters")}</Table.ColumnHeader>
            <Table.ColumnHeader>
              {t("factors.requiredFields")}
            </Table.ColumnHeader>
            <Table.ColumnHeader>{t("factors.status")}</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {factors.length === 0 ? (
            <Table.Row>
              <Table.Cell colSpan={7} textAlign="center" py={8}>
                <Text color="gray.500" fontSize="lg">
                  {t("factors.noFactors")}
                </Text>
              </Table.Cell>
            </Table.Row>
          ) : (
            factors.map((factor: any) => (
              <Table.Row key={factor.name}>
                <Table.Cell fontWeight="medium">{factor.name}</Table.Cell>
                <Table.Cell>
                  <Text color="blue.600">
                    {t(`factors.${factor.factor_type}`)}
                  </Text>
                </Table.Cell>
                <Table.Cell>
                  <Text fontSize="xs" color="purple.600" fontFamily="mono">
                    {factor.factor_class || "-"}
                  </Text>
                </Table.Cell>
                <Table.Cell>
                  <Text color="gray.600" fontSize="sm">
                    {factor.description}
                  </Text>
                </Table.Cell>
                <Table.Cell>
                  <Text fontSize="xs" color="gray.500">
                    {factor.parameters &&
                    Object.keys(factor.parameters).length > 0
                      ? Object.entries(factor.parameters)
                          .map(([key, value]) => `${key}=${value}`)
                          .join(", ")
                      : "-"}
                  </Text>
                </Table.Cell>
                <Table.Cell>
                  <Text fontSize="xs" color="gray.500">
                    {factor.required_fields && factor.required_fields.length > 0
                      ? factor.required_fields.join(", ")
                      : "-"}
                  </Text>
                </Table.Cell>
                <Table.Cell>
                  <Text
                    color={
                      factor.status === "active" ? "green.600" : "gray.500"
                    }
                    fontSize="sm"
                  >
                    {t(`factors.${factor.status}`)}
                  </Text>
                </Table.Cell>
              </Table.Row>
            ))
          )}
        </Table.Body>
      </Table.Root>
    </Box>
  );
}

export default FactorList;

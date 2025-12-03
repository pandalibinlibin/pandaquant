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
        url: "/api/v1/factors/classes",
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
            <Table.ColumnHeader w="20%">{t("factors.className")}</Table.ColumnHeader>
            <Table.ColumnHeader w="12%">{t("factors.factorType")}</Table.ColumnHeader>
            <Table.ColumnHeader w="12%">{t("factors.module")}</Table.ColumnHeader>
            <Table.ColumnHeader w="20%">{t("factors.parameters")}</Table.ColumnHeader>
            <Table.ColumnHeader w="20%">{t("factors.requiredFields")}</Table.ColumnHeader>
            <Table.ColumnHeader w="16%">{t("factors.description")}</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {factors.length === 0 ? (
            <Table.Row>
              <Table.Cell colSpan={6} textAlign="center" py={8}>
                <Text color="gray.500" fontSize="lg">
                  {t("factors.noFactors")}
                </Text>
              </Table.Cell>
            </Table.Row>
          ) : (
            factors.map((factor: any) => (
              <Table.Row key={factor.class_name}>
                <Table.Cell fontWeight="medium" color="blue.600">
                  {factor.display_name}
                </Table.Cell>
                <Table.Cell>
                  <Text fontSize="sm" color="purple.600">
                    {factor.factor_type}
                  </Text>
                </Table.Cell>
                <Table.Cell>
                  <Text fontSize="sm" color="gray.600">
                    {factor.module}
                  </Text>
                </Table.Cell>
                <Table.Cell>
                  <Text fontSize="xs" color="gray.600">
                    {factor.parameters && factor.parameters.length > 0
                      ? factor.parameters
                          .map(
                            (p: any) =>
                              `${p.name}: ${p.type}${p.default !== undefined && p.default !== null ? ` = ${p.default}` : ""}`
                          )
                          .join(", ")
                      : "-"}
                  </Text>
                </Table.Cell>
                <Table.Cell>
                  <Text fontSize="xs" color="gray.600">
                    {factor.required_fields && factor.required_fields.length > 0
                      ? factor.required_fields.join(", ")
                      : "-"}
                  </Text>
                </Table.Cell>
                <Table.Cell>
                  <Text fontSize="xs" color="gray.500">
                    {factor.description}
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

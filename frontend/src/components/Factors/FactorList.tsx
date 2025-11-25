import { Box, Text, Spinner } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";
import { useState } from "react";

interface FactorListProps {
  factorType?: string;
}

// @ts-ignore
function FactorList({ factorType }: FactorListProps) {
  const { t } = useTranslation();
  // @ts-ignore
  const [factors, setFactors] = useState<any[]>([]);
  // @ts-ignore
  const [loading, setLoading] = useState(false);
  // @ts-ignore
  const [error, setError] = useState<string | null>(null);

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
      <Text fontSize="lg" fontWeight="bold" mb={4}>
        {t("factors.title")}
      </Text>

      <Text color="gray.500" fontSize="sm">
        共 {factors.length} 个因子
      </Text>

      {factors.length === 0 ? (
        <Box textAlign="center" py={8}>
          <Text color="gray.500" fontSize="lg">
            {t("factors.noFactors")}
          </Text>
        </Box>
      ) : (
        <Text color="blue.500" mt={4}>
          因子列表将在这里显示...
        </Text>
      )}
    </Box>
  );
}

export default FactorList;

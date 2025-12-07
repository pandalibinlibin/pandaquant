import { Box, Flex, Icon, Text } from "@chakra-ui/react";
import { useQueryClient } from "@tanstack/react-query";
import { Link as RouterLink, useLocation } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import {
  FiActivity,
  FiBarChart2,
  FiDatabase,
  FiGrid,
  FiHome,
  FiSettings,
  FiTrendingUp,
  FiUsers,
} from "react-icons/fi";
import type { IconType } from "react-icons/lib";

import type { UserPublic } from "@/client";

interface SidebarItemsProps {
  onClose?: () => void;
}

interface Item {
  icon: IconType;
  title: string;
  path: string;
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"]);
  const location = useLocation();

  const menuItems: Item[] = [
    { icon: FiHome, title: t("navigation.dashboard"), path: "/" },
    { icon: FiDatabase, title: t("navigation.data"), path: "/data" },
    { icon: FiGrid, title: t("navigation.factors"), path: "/factors" },
    {
      icon: FiTrendingUp,
      title: t("navigation.strategies"),
      path: "/strategies",
    },
    { icon: FiBarChart2, title: t("navigation.backtests"), path: "/backtests" },
    { icon: FiSettings, title: t("navigation.settings"), path: "/settings" },
  ];

  const finalItems: Item[] = currentUser?.is_superuser
    ? [
        ...menuItems,
        { icon: FiUsers, title: t("navigation.admin"), path: "/admin" },
      ]
    : menuItems;

  const listItems = finalItems.map(({ icon, title, path }) => {
    const isActive = location.pathname === path;

    return (
      <RouterLink key={title} to={path} onClick={onClose}>
        <Flex
          gap={4}
          px={4}
          py={2}
          bg={isActive ? "blue.500" : "transparent"}
          color={isActive ? "white" : "inherit"}
          _hover={{
            background: isActive ? "blue.600" : "gray.subtle",
          }}
          alignItems="center"
          fontSize="sm"
        >
          <Icon as={icon} alignSelf="center" />
          <Text ml={2}>{title}</Text>
        </Flex>
      </RouterLink>
    );
  });

  return (
    <>
      <Text fontSize="xs" px={4} py={2} fontWeight="bold">
        Menu
      </Text>
      <Box>{listItems}</Box>
    </>
  );
};

export default SidebarItems;

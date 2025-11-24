import { Button, HStack, Text } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";
import { useState, useEffect } from "react";

function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const [currentLang, setCurrentLang] = useState(i18n.language);

  useEffect(() => {
    const handleLanguageChanged = () => {
      setCurrentLang(i18n.language);
    };

    i18n.on("languageChanged", handleLanguageChanged);

    return () => {
      i18n.off("languageChanged", handleLanguageChanged);
    };
  }, [i18n]);

  const toggleLanguage = () => {
    const newLang = currentLang === "zh-CN" ? "en-US" : "zh-CN";
    i18n.changeLanguage(newLang);
  };

  const getLanguageDisplay = (lang: string) => {
    return lang === "zh-CN" ? "中文" : "English";
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleLanguage}
      _hover={{ bg: "gray.100" }}
    >
      <HStack gap={1}>
        <Text fontSize="sm">🌍</Text>
        <Text fontSize="sm">{getLanguageDisplay(currentLang)}</Text>
      </HStack>
    </Button>
  );
}

export default LanguageSwitcher;

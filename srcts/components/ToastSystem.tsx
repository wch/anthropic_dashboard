import React, { useEffect } from "react";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";

export function ToastSystem() {
  useEffect(() => {
    // Register custom message handler for warnings from the Shiny server
    const handleWarningMessage = (msg: { message: string; type: string }) => {
      switch (msg.type) {
        case "warning":
          toast.warning(msg.message, {
            duration: 8000, // Show warnings for 8 seconds
            action: {
              label: "Dismiss",
              onClick: () => {},
            },
          });
          break;
        case "error":
          toast.error(msg.message, {
            duration: 10000, // Show errors for 10 seconds
            action: {
              label: "Dismiss", 
              onClick: () => {},
            },
          });
          break;
        case "info":
          toast.info(msg.message, {
            duration: 5000,
          });
          break;
        case "success":
          toast.success(msg.message, {
            duration: 4000,
          });
          break;
        default:
          toast(msg.message, {
            duration: 5000,
          });
      }
    };

    // Register the message handler when Shiny is available
    const registerHandler = () => {
      if (window.Shiny && window.Shiny.addCustomMessageHandler) {
        window.Shiny.addCustomMessageHandler("warning", handleWarningMessage);
        console.log("Toast system: Registered warning message handler");
      } else {
        // Retry until Shiny is available
        setTimeout(registerHandler, 100);
      }
    };

    registerHandler();

    // Cleanup function (though Shiny doesn't provide removeCustomMessageHandler)
    return () => {
      // No cleanup needed for Shiny message handlers
    };
  }, []);

  return <Toaster position="top-right" />;
}
"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";

import {
  createRoleBinding,
  createApiKey,
  createClientApp,
  createTenant,
  createUser,
  disableMfa,
  listApiKeys,
  listRoleBindings,
  revokeConsent,
  revokeApiKey,
  resendMfa,
  rotateApiKey,
  setupMfa,
  updateClientApp,
  updateRoleBinding,
  updateTenant,
  updateUser,
  verifyMfa,
} from "@/features/admin/api";
import { authStore } from "@/features/auth/store/auth-store";

export function useAdminConsole() {
  const queryClient = useQueryClient();
  const tenantId = authStore((state) => state.session?.user?.tenantId);
  const hydrated = authStore((state) => state.hydrated);

  const apiKeysQuery = useQuery({
    queryKey: ["api-keys", tenantId],
    queryFn: () => listApiKeys(tenantId),
    enabled: Boolean(tenantId && hydrated),
  });

  const roleBindingsQuery = useQuery({
    queryKey: ["role-bindings", tenantId],
    queryFn: () => listRoleBindings(tenantId),
    enabled: Boolean(tenantId && hydrated),
  });

  const invalidateAdminData = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["tenants"] }),
      queryClient.invalidateQueries({ queryKey: ["users"] }),
      queryClient.invalidateQueries({ queryKey: ["client-apps"] }),
      queryClient.invalidateQueries({ queryKey: ["api-keys"] }),
      queryClient.invalidateQueries({ queryKey: ["audit-logs"] }),
      queryClient.invalidateQueries({ queryKey: ["consents"] }),
      queryClient.invalidateQueries({ queryKey: ["role-bindings"] }),
      queryClient.invalidateQueries({ queryKey: ["telemetry-summary"] }),
    ]);
  };

  const tenantMutation = useMutation({
    mutationFn: createTenant,
    onSuccess: async () => {
      toast.success("Tenant criado.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao criar tenant."),
  });

  const tenantUpdateMutation = useMutation({
    mutationFn: ({ tenantId, payload }: { tenantId: string; payload: Parameters<typeof updateTenant>[1] }) => updateTenant(tenantId, payload),
    onSuccess: async () => {
      toast.success("Tenant atualizado.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao atualizar tenant."),
  });

  const userMutation = useMutation({
    mutationFn: createUser,
    onSuccess: async () => {
      toast.success("Usuario criado.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao criar usuario."),
  });

  const userUpdateMutation = useMutation({
    mutationFn: ({ userId, payload }: { userId: string; payload: Parameters<typeof updateUser>[1] }) => updateUser(userId, payload),
    onSuccess: async () => {
      toast.success("Usuario atualizado.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao atualizar usuario."),
  });

  const clientAppMutation = useMutation({
    mutationFn: createClientApp,
    onSuccess: async (result) => {
      toast.success(result.client_secret ? "Aplicacao criada. Salve o client secret agora." : "Aplicacao criada.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao criar aplicacao."),
  });

  const clientAppUpdateMutation = useMutation({
    mutationFn: ({ clientAppId, payload }: { clientAppId: string; payload: Parameters<typeof updateClientApp>[1] }) =>
      updateClientApp(clientAppId, payload),
    onSuccess: async () => {
      toast.success("Aplicacao atualizada.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao atualizar aplicacao."),
  });

  const apiKeyMutation = useMutation({
    mutationFn: createApiKey,
    onSuccess: async () => {
      toast.success("API Key criada.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao criar API Key."),
  });

  const apiKeyRevokeMutation = useMutation({
    mutationFn: revokeApiKey,
    onSuccess: async () => {
      toast.success("API Key revogada.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao revogar API Key."),
  });

  const apiKeyRotateMutation = useMutation({
    mutationFn: rotateApiKey,
    onSuccess: async () => {
      toast.success("API Key rotacionada.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao rotacionar API Key."),
  });

  const consentRevokeMutation = useMutation({
    mutationFn: revokeConsent,
    onSuccess: async () => {
      toast.success("Consentimento revogado.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao revogar consentimento."),
  });

  const roleBindingMutation = useMutation({
    mutationFn: createRoleBinding,
    onSuccess: async () => {
      toast.success("Acesso por aplicacao criado.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao criar acesso por aplicacao."),
  });

  const roleBindingUpdateMutation = useMutation({
    mutationFn: ({ roleBindingId, payload }: { roleBindingId: string; payload: Parameters<typeof updateRoleBinding>[1] }) =>
      updateRoleBinding(roleBindingId, payload),
    onSuccess: async () => {
      toast.success("Acesso por aplicacao atualizado.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao atualizar acesso por aplicacao."),
  });

  const mfaSetupMutation = useMutation({
    mutationFn: setupMfa,
    onError: () => toast.error("Falha ao preparar o MFA."),
  });

  const mfaVerifyMutation = useMutation({
    mutationFn: verifyMfa,
    onSuccess: async () => {
      toast.success("MFA ativado.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao ativar o MFA."),
  });

  const mfaDisableMutation = useMutation({
    mutationFn: disableMfa,
    onSuccess: async () => {
      toast.success("MFA desativado.");
      await invalidateAdminData();
    },
    onError: () => toast.error("Falha ao desativar o MFA."),
  });

  const mfaResendMutation = useMutation({
    mutationFn: resendMfa,
    onSuccess: () => toast.success("Codigo MFA reenviado por e-mail."),
    onError: () => toast.error("Falha ao reenviar o codigo MFA."),
  });

  return {
    apiKeysQuery,
    roleBindingsQuery,
    tenantMutation,
    tenantUpdateMutation,
    userMutation,
    userUpdateMutation,
    clientAppMutation,
    clientAppUpdateMutation,
    apiKeyMutation,
    apiKeyRevokeMutation,
    apiKeyRotateMutation,
    consentRevokeMutation,
    roleBindingMutation,
    roleBindingUpdateMutation,
    mfaSetupMutation,
    mfaVerifyMutation,
    mfaDisableMutation,
    mfaResendMutation,
  };
}

from __future__ import annotations

from app.models import Tenant, User


def render_welcome_email(tenant: Tenant, user: User, temporary_password: bool = False) -> tuple[str, str]:
    branding = tenant.branding
    subject = f"Bem-vindo ao {tenant.name}"
    headline = branding.login_title or "Acesse sua conta"
    support_email = branding.support_email or tenant.contact_email
    password_line = (
        "<p style='margin:16px 0 0;color:#5b6574'>Sua senha inicial foi provisionada com seguranca. Recomendamos altera-la no primeiro acesso.</p>"
        if temporary_password
        else ""
    )
    html = f"""
    <div style="font-family:{branding.font_family or 'sans-serif'};background:#f7f1e7;padding:32px">
      <div style="max-width:560px;margin:0 auto;background:#fffaf2;border:1px solid #eadfce;border-radius:24px;padding:32px">
        <p style="letter-spacing:.22em;text-transform:uppercase;font-size:11px;color:#7a8391">Sylo SSO</p>
        <h1 style="margin:12px 0 0;color:{branding.secondary_color};font-size:28px">{headline}</h1>
        <p style="margin:16px 0 0;color:#111827">Ola, {user.name}. Sua conta no tenant <strong>{tenant.name}</strong> foi provisionada.</p>
        {password_line}
        <p style="margin:24px 0 0;color:#5b6574">Precisa de ajuda? Contate {support_email}.</p>
      </div>
    </div>
    """
    return subject, html


def render_security_notification_email(tenant: Tenant, user: User, message: str) -> tuple[str, str]:
    subject = f"Alerta de seguranca no {tenant.name}"
    html = f"""
    <div style="font-family:{tenant.branding.font_family or 'sans-serif'};background:#f7f1e7;padding:32px">
      <div style="max-width:560px;margin:0 auto;background:#fffaf2;border:1px solid #eadfce;border-radius:24px;padding:32px">
        <h1 style="margin:0;color:{tenant.branding.secondary_color};font-size:24px">Notificacao de seguranca</h1>
        <p style="margin:16px 0 0;color:#111827">Ola, {user.name}.</p>
        <p style="margin:12px 0 0;color:#5b6574">{message}</p>
      </div>
    </div>
    """
    return subject, html


def render_password_reset_email(tenant: Tenant, user: User, reset_url: str) -> tuple[str, str]:
    subject = f"Redefinicao de senha no {tenant.name}"
    html = f"""
    <div style="font-family:{tenant.branding.font_family or 'sans-serif'};background:#f7f1e7;padding:32px">
      <div style="max-width:560px;margin:0 auto;background:#fffaf2;border:1px solid #eadfce;border-radius:24px;padding:32px">
        <h1 style="margin:0;color:{tenant.branding.secondary_color};font-size:24px">Recuperacao de senha</h1>
        <p style="margin:16px 0 0;color:#111827">Ola, {user.name}.</p>
        <p style="margin:12px 0 0;color:#5b6574">Recebemos uma solicitacao para redefinir sua senha.</p>
        <p style="margin:20px 0 0">
          <a href="{reset_url}" style="display:inline-block;background:{tenant.branding.primary_color};color:#fff;padding:12px 18px;border-radius:999px;text-decoration:none">Redefinir senha</a>
        </p>
      </div>
    </div>
    """
    return subject, html


def render_email_verification_email(tenant: Tenant, user: User, verification_url: str) -> tuple[str, str]:
    subject = f"Confirme seu e-mail no {tenant.name}"
    html = f"""
    <div style="font-family:{tenant.branding.font_family or 'sans-serif'};background:#f7f1e7;padding:32px">
      <div style="max-width:560px;margin:0 auto;background:#fffaf2;border:1px solid #eadfce;border-radius:24px;padding:32px">
        <h1 style="margin:0;color:{tenant.branding.secondary_color};font-size:24px">Confirmacao de e-mail</h1>
        <p style="margin:16px 0 0;color:#111827">Ola, {user.name}.</p>
        <p style="margin:12px 0 0;color:#5b6574">Antes de acessar os aplicativos do tenant, confirme seu e-mail.</p>
        <p style="margin:20px 0 0">
          <a href="{verification_url}" style="display:inline-block;background:{tenant.branding.primary_color};color:#fff;padding:12px 18px;border-radius:999px;text-decoration:none">Confirmar e-mail</a>
        </p>
      </div>
    </div>
    """
    return subject, html


def render_mfa_code_email(tenant: Tenant, user: User, code: str) -> tuple[str, str]:
    subject = f"Seu codigo de verificacao no {tenant.name}"
    html = f"""
    <div style="font-family:{tenant.branding.font_family or 'sans-serif'};background:#f7f1e7;padding:32px">
      <div style="max-width:560px;margin:0 auto;background:#fffaf2;border:1px solid #eadfce;border-radius:24px;padding:32px">
        <h1 style="margin:0;color:{tenant.branding.secondary_color};font-size:24px">Verificacao em duas etapas</h1>
        <p style="margin:16px 0 0;color:#111827">Ola, {user.name}.</p>
        <p style="margin:12px 0 0;color:#5b6574">Use o codigo abaixo para concluir o acesso ao Sylo SSO.</p>
        <p style="margin:20px 0 0;font-size:32px;letter-spacing:.18em;color:{tenant.branding.secondary_color};font-weight:700">{code}</p>
        <p style="margin:16px 0 0;color:#5b6574">Se voce nao solicitou este acesso, ignore esta mensagem.</p>
      </div>
    </div>
    """
    return subject, html

from flask_openapi3 import APIBlueprint, Tag

from app.modules.tenants.schemas import TenantSlugPathSchema
from app.modules.tenants.service import WhiteLabelService


external_tag = Tag(name="Tenants External")
tenants_external_api = APIBlueprint("tenants_external_api", __name__, abp_tags=[external_tag])


@tenants_external_api.get("/branding/<tenant_slug>", summary="Get public tenant branding")
def get_public_branding(path: TenantSlugPathSchema):
    return WhiteLabelService.get_by_slug(path.tenant_slug), 200

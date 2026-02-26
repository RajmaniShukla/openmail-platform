"""
OpenMail Platform - Domain Endpoints
"""
from typing import Annotated, List
from uuid import UUID
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import generate_dkim_keypair
from app.db.database import get_db
from app.models.user import User
from app.models.domain import Domain, DNSRecord
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.domain import (
    DomainCreate,
    DomainResponse,
    DomainVerifyResponse,
    DomainDNSResponse,
    DNSRecordResponse
)
from app.schemas.auth import MessageResponse

router = APIRouter()


@router.get("", response_model=List[DomainResponse])
async def list_domains(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """List user's domains."""
    result = await db.execute(
        select(Domain)
        .where(Domain.owner_id == current_user.id)
        .options(selectinload(Domain.dns_records))
        .order_by(Domain.name)
    )
    domains = result.scalars().all()
    
    return [DomainResponse.model_validate(d) for d in domains]


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def add_domain(
    domain_data: DomainCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Add a new domain."""
    domain_name = domain_data.name.lower().strip()
    
    # Check if domain already exists
    result = await db.execute(
        select(Domain).where(Domain.name == domain_name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain already registered"
        )
    
    # Generate DKIM keys
    dkim_keys = generate_dkim_keypair()
    
    # Create domain
    domain = Domain(
        name=domain_name,
        owner_id=current_user.id,
        verification_token=secrets.token_urlsafe(32),
        dkim_private_key=dkim_keys["private_key"],
        dkim_public_key=dkim_keys["public_key"]
    )
    db.add(domain)
    await db.flush()
    
    # Create DNS records
    dns_records = [
        # Verification record
        DNSRecord(
            domain_id=domain.id,
            record_type="TXT",
            name=f"_openmail-verify.{domain_name}",
            value=f"openmail-verification={domain.verification_token}",
            purpose="verification"
        ),
        # MX record
        DNSRecord(
            domain_id=domain.id,
            record_type="MX",
            name=domain_name,
            value=settings.MAIL_SERVER_HOSTNAME,
            priority=10,
            purpose="mx"
        ),
        # SPF record
        DNSRecord(
            domain_id=domain.id,
            record_type="TXT",
            name=domain_name,
            value=f"v=spf1 include:{settings.MAIL_SERVER_HOSTNAME} ~all",
            purpose="spf"
        ),
        # DKIM record
        DNSRecord(
            domain_id=domain.id,
            record_type="TXT",
            name=f"{domain.dkim_selector}._domainkey.{domain_name}",
            value=f"v=DKIM1; k=rsa; p={dkim_keys['public_key_dns']}",
            purpose="dkim"
        ),
        # DMARC record
        DNSRecord(
            domain_id=domain.id,
            record_type="TXT",
            name=f"_dmarc.{domain_name}",
            value=f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{settings.MAIL_SERVER_HOSTNAME}",
            purpose="dmarc"
        )
    ]
    
    for record in dns_records:
        db.add(record)
    
    await db.commit()
    await db.refresh(domain)
    
    # Load DNS records
    result = await db.execute(
        select(Domain)
        .where(Domain.id == domain.id)
        .options(selectinload(Domain.dns_records))
    )
    domain = result.scalar_one()
    
    return DomainResponse.model_validate(domain)


@router.post("/{domain_id}/verify", response_model=DomainVerifyResponse)
async def verify_domain(
    domain_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Verify domain DNS configuration."""
    import dns.resolver
    
    result = await db.execute(
        select(Domain)
        .where(
            Domain.id == domain_id,
            Domain.owner_id == current_user.id
        )
        .options(selectinload(Domain.dns_records))
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    
    checks = {
        "verification": {"status": "fail", "found": None},
        "mx": {"status": "fail", "found": None},
        "spf": {"status": "fail", "found": None},
        "dkim": {"status": "fail", "found": None},
        "dmarc": {"status": "fail", "found": None}
    }
    
    try:
        # Check verification TXT record
        try:
            answers = dns.resolver.resolve(f"_openmail-verify.{domain.name}", "TXT")
            for rdata in answers:
                txt_value = rdata.to_text().strip('"')
                if f"openmail-verification={domain.verification_token}" in txt_value:
                    checks["verification"]["status"] = "pass"
                    checks["verification"]["found"] = txt_value
                    break
        except Exception:
            pass
        
        # Check MX record
        try:
            answers = dns.resolver.resolve(domain.name, "MX")
            for rdata in answers:
                mx_host = str(rdata.exchange).rstrip('.')
                checks["mx"]["found"] = mx_host
                if settings.MAIL_SERVER_HOSTNAME in mx_host:
                    checks["mx"]["status"] = "pass"
                    break
        except Exception:
            pass
        
        # Check SPF record
        try:
            answers = dns.resolver.resolve(domain.name, "TXT")
            for rdata in answers:
                txt_value = rdata.to_text().strip('"')
                if txt_value.startswith("v=spf1"):
                    checks["spf"]["found"] = txt_value
                    if settings.MAIL_SERVER_HOSTNAME in txt_value:
                        checks["spf"]["status"] = "pass"
                    break
        except Exception:
            pass
        
        # Check DKIM record
        try:
            dkim_name = f"{domain.dkim_selector}._domainkey.{domain.name}"
            answers = dns.resolver.resolve(dkim_name, "TXT")
            for rdata in answers:
                txt_value = rdata.to_text().strip('"')
                if "v=DKIM1" in txt_value:
                    checks["dkim"]["status"] = "pass"
                    checks["dkim"]["found"] = txt_value[:100] + "..."
                    break
        except Exception:
            pass
        
        # Check DMARC record
        try:
            answers = dns.resolver.resolve(f"_dmarc.{domain.name}", "TXT")
            for rdata in answers:
                txt_value = rdata.to_text().strip('"')
                if txt_value.startswith("v=DMARC1"):
                    checks["dmarc"]["status"] = "pass"
                    checks["dmarc"]["found"] = txt_value
                    break
        except Exception:
            pass
        
    except Exception as e:
        pass
    
    # Determine if domain is verified
    is_verified = all(
        checks[check]["status"] == "pass" 
        for check in ["verification", "mx"]
    )
    
    if is_verified and not domain.is_verified:
        domain.is_verified = True
        domain.verified_at = datetime.utcnow()
        
        # Update DNS records verification status
        for record in domain.dns_records:
            if record.purpose in checks:
                record.is_verified = checks[record.purpose]["status"] == "pass"
        
        await db.commit()
    
    return DomainVerifyResponse(
        is_verified=is_verified,
        checks=checks
    )


@router.get("/{domain_id}/dns-records", response_model=DomainDNSResponse)
async def get_dns_records(
    domain_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get required DNS records for a domain."""
    result = await db.execute(
        select(Domain)
        .where(
            Domain.id == domain_id,
            Domain.owner_id == current_user.id
        )
        .options(selectinload(Domain.dns_records))
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    
    return DomainDNSResponse(
        domain=domain.name,
        records=[DNSRecordResponse.model_validate(r) for r in domain.dns_records]
    )


@router.delete("/{domain_id}", response_model=MessageResponse)
async def delete_domain(
    domain_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Delete a domain."""
    result = await db.execute(
        select(Domain).where(
            Domain.id == domain_id,
            Domain.owner_id == current_user.id
        )
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    
    await db.delete(domain)
    await db.commit()
    
    return MessageResponse(
        message="Domain deleted successfully",
        success=True
    )

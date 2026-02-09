"""
Campaign endpoints for CRUD operations.
All endpoints require JWT authentication.
"""
from fastapi import APIRouter, Depends, status
from app.models.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignWithStats,
    CampaignListResponse
)
from app.services.campaign_service import CampaignService
from app.dependencies import get_current_user


router = APIRouter()


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new campaign.

    Requires authentication. Campaign will be associated with the authenticated user.

    Args:
        campaign_data: Campaign creation data
        current_user: Decoded JWT payload from get_current_user dependency

    Returns:
        Created campaign data

    Raises:
        AppError: If campaign creation fails
    """
    service = CampaignService()
    user_id = current_user.get("sub")
    campaign = service.create(user_id=user_id, campaign_data=campaign_data)
    return CampaignResponse(**campaign)


@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(current_user: dict = Depends(get_current_user)):
    """
    List all campaigns for the authenticated user.

    Requires authentication.

    Args:
        current_user: Decoded JWT payload from get_current_user dependency

    Returns:
        List of campaigns with total count

    Raises:
        AppError: If listing fails
    """
    service = CampaignService()
    user_id = current_user.get("sub")
    campaigns = service.list_for_user(user_id=user_id)
    return CampaignListResponse(
        campaigns=[CampaignResponse(**c) for c in campaigns],
        total=len(campaigns)
    )


@router.get("/{campaign_id}", response_model=CampaignWithStats)
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a single campaign by ID with statistics.

    Requires authentication. User can only access their own campaigns.

    Args:
        campaign_id: ID of the campaign
        current_user: Decoded JWT payload from get_current_user dependency

    Returns:
        Campaign data with statistics

    Raises:
        AppError: If campaign not found or access denied
    """
    service = CampaignService()
    user_id = current_user.get("sub")
    campaign = service.get_by_id(user_id=user_id, campaign_id=campaign_id)
    return CampaignWithStats(**campaign)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    update_data: CampaignUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a campaign.

    Requires authentication. User can only update their own campaigns.

    Args:
        campaign_id: ID of the campaign
        update_data: Campaign update data
        current_user: Decoded JWT payload from get_current_user dependency

    Returns:
        Updated campaign data

    Raises:
        AppError: If campaign not found or update fails
    """
    service = CampaignService()
    user_id = current_user.get("sub")
    campaign = service.update(user_id=user_id, campaign_id=campaign_id, update_data=update_data)
    return CampaignResponse(**campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a campaign.

    Requires authentication. User can only delete their own campaigns.

    Args:
        campaign_id: ID of the campaign
        current_user: Decoded JWT payload from get_current_user dependency

    Returns:
        No content (204)

    Raises:
        AppError: If campaign not found or deletion fails
    """
    service = CampaignService()
    user_id = current_user.get("sub")
    service.delete(user_id=user_id, campaign_id=campaign_id)

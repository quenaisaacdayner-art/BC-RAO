"""
Campaign service for CRUD operations.
Handles campaign creation, listing, updating, and deletion with Supabase.
"""
from typing import Optional
from fastapi import status
from app.integrations.supabase_client import get_supabase_client
from app.models.campaign import CampaignCreate, CampaignUpdate
from app.utils.errors import AppError, ErrorCode


class CampaignService:
    """Service class for campaign operations."""

    def __init__(self):
        self.supabase = get_supabase_client()

    def create(self, user_id: str, campaign_data: CampaignCreate) -> dict:
        """
        Create a new campaign for the user.

        Args:
            user_id: ID of the authenticated user
            campaign_data: Campaign creation data

        Returns:
            Created campaign data

        Raises:
            AppError: If campaign creation fails
        """
        try:
            # Convert HttpUrl to string if present
            campaign_dict = campaign_data.model_dump()
            if campaign_dict.get("product_url"):
                campaign_dict["product_url"] = str(campaign_dict["product_url"])

            # Add user_id and default status
            campaign_dict["user_id"] = user_id
            campaign_dict["status"] = "active"

            response = self.supabase.table("campaigns").insert(campaign_dict).execute()

            if not response.data:
                raise AppError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Failed to create campaign",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return response.data[0]

        except AppError:
            raise
        except Exception as e:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to create campaign: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list_for_user(self, user_id: str) -> list[dict]:
        """
        List all campaigns for a user.

        Args:
            user_id: ID of the authenticated user

        Returns:
            List of campaigns

        Raises:
            AppError: If listing fails
        """
        try:
            response = self.supabase.table("campaigns")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()

            return response.data

        except Exception as e:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to list campaigns: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_by_id(self, user_id: str, campaign_id: str) -> dict:
        """
        Get a single campaign by ID with statistics.

        Args:
            user_id: ID of the authenticated user
            campaign_id: ID of the campaign

        Returns:
            Campaign data with stats

        Raises:
            AppError: If campaign not found or access denied
        """
        try:
            response = self.supabase.table("campaigns")\
                .select("*")\
                .eq("id", campaign_id)\
                .eq("user_id", user_id)\
                .execute()

            if not response.data:
                raise AppError(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message="Campaign not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            campaign = response.data[0]

            # Add stats (placeholders for now, will be populated in future phases)
            campaign["stats"] = {
                "posts_collected": 0,
                "drafts_generated": 0,
                "active_monitors": 0
            }

            return campaign

        except AppError:
            raise
        except Exception as e:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get campaign: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, user_id: str, campaign_id: str, update_data: CampaignUpdate) -> dict:
        """
        Update a campaign.

        Args:
            user_id: ID of the authenticated user
            campaign_id: ID of the campaign
            update_data: Campaign update data

        Returns:
            Updated campaign data

        Raises:
            AppError: If campaign not found or update fails
        """
        try:
            # First verify campaign exists and belongs to user
            self.get_by_id(user_id, campaign_id)

            # Convert HttpUrl to string if present and filter out None values
            update_dict = update_data.model_dump(exclude_none=True)
            if update_dict.get("product_url"):
                update_dict["product_url"] = str(update_dict["product_url"])

            if not update_dict:
                raise AppError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="No fields to update",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            response = self.supabase.table("campaigns")\
                .update(update_dict)\
                .eq("id", campaign_id)\
                .eq("user_id", user_id)\
                .execute()

            if not response.data:
                raise AppError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Failed to update campaign",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return response.data[0]

        except AppError:
            raise
        except Exception as e:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to update campaign: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, user_id: str, campaign_id: str) -> None:
        """
        Delete a campaign.

        Args:
            user_id: ID of the authenticated user
            campaign_id: ID of the campaign

        Raises:
            AppError: If campaign not found or deletion fails
        """
        try:
            # First verify campaign exists and belongs to user
            self.get_by_id(user_id, campaign_id)

            response = self.supabase.table("campaigns")\
                .delete()\
                .eq("id", campaign_id)\
                .eq("user_id", user_id)\
                .execute()

            # Delete successful (no data returned for delete operations is normal)

        except AppError:
            raise
        except Exception as e:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to delete campaign: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

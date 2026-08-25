from pydantic import BaseModel, Field


class WechatLoginRequest(BaseModel):
    code: str = Field(min_length=1, max_length=256, description="uni.login 返回的临时 code")
    nickname: str | None = Field(default=None, max_length=100, description="微信小程序昵称")
    avatar_url: str | None = Field(default=None, max_length=500, description="上传至腾讯云 COS 后的头像地址")


class UpdateUserProfileRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=100, description="用户昵称")
    avatar_url: str = Field(min_length=1, max_length=500, description="腾讯云 COS 头像地址")

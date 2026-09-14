import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, InputText

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==================== الأيديهات الأساسية ====================
MY_USER_ID = 1054739108905361469              
CREATE_VC_ID = 1054739108905361469            # أيدي روم Tap to Create

HIGH_STAFF_ROLE_IDS = [
    1054739108905361469, 
    1548474673124081795  
]
# ============================================================

active_temp_vcs = {}  # {channel_id: owner_id}

@bot.event
async def on_ready():
    print(f"✅ TEMP-VC BOT IS ONLINE: {bot.user}")

# ==================== نافذة تغيير اسم الروم ====================
class RenameModal(Modal):
    def __init__(self, voice_channel):
        super().__init__(title="تغيير اسم روم الصوت")
        self.voice_channel = voice_channel
        self.new_name = InputText(
            label="اسم الروم الجديد", 
            placeholder="اكتب الاسم هنا...", 
            max_length=50,
            required=True
        )
        self.add_item(self.new_name)

    async def callback(self, interaction: discord.Interaction):
        await self.voice_channel.edit(name=self.new_name.value)
        await interaction.response.send_message(f"✅ تم تغيير اسم الروم إلى: **{self.new_name.value}**", ephemeral=True)

# ==================== أزرار التحكم في الـ Temp-VC ====================
class TempControlView(View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id and interaction.user.id != MY_USER_ID and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ هذه ليست رومك الخاصة!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.red, emoji="🔒", custom_id="vc_lock_btn")
    async def lock_btn(self, interaction: discord.Interaction, button: Button):
        vc = interaction.user.voice.channel
        await vc.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 **تم قفل الروم بنجاح.**", ephemeral=True)

    @discord.ui.button(label="Unlock", style=discord.ButtonStyle.green, emoji="🔓", custom_id="vc_unlock_btn")
    async def unlock_btn(self, interaction: discord.Interaction, button: Button):
        vc = interaction.user.voice.channel
        await vc.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 **تم فتح الروم للجميع.**", ephemeral=True)

    @discord.ui.button(label="Rename", style=discord.ButtonStyle.blurple, emoji="✏️", custom_id="vc_rename_btn")
    async def rename_btn(self, interaction: discord.Interaction, button: Button):
        vc = interaction.user.voice.channel
        await interaction.response.send_modal(RenameModal(vc))

    @discord.ui.button(label="Get Staff", style=discord.ButtonStyle.grey, emoji="🚨", custom_id="vc_get_staff_btn")
    async def get_staff_btn(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.voice or interaction.user.voice.channel != interaction.channel:
            await interaction.response.send_message("❌ يجب أن تكون داخل الروم لطلب المشرفين!", ephemeral=True)
            return
        
        staff_mentions = " ".join([f"<@&{role_id}>" for role_id in HIGH_STAFF_ROLE_IDS])
        await interaction.channel.send(f"🚨 **نداء عاجل من {interaction.user.mention}!** {staff_mentions} يرجى الدخول إلى الروم الصوتية فوراً.")
        await interaction.response.send_message("✅ تم إرسال النداء للمشرفين بنجاح.", ephemeral=True)

# ==================== أحداث الـ Voice (إنشاء وحذف الرومات المؤقتة) ====================
@bot.event
async def on_voice_state_update(member, before, after):
    # إنشاء Temp-VC عند الدخول لروم الـ Create
    if after.channel and after.channel.id == CREATE_VC_ID:
        category = after.channel.category
        new_vc = await member.guild.create_voice_channel(
            name=f"🔊 {member.name}'s Room",
            category=category,
            user_limit=10
        )
        await new_vc.set_permissions(member, connect=True, manage_channels=True, mute_members=True, move_members=True)
        await member.edit(voice_channel=new_vc)
        active_temp_vcs[new_vc.id] = member.id

        embed = discord.Embed(
            title=f"🎛️ لوحة تحكم روم: {member.name}",
            description="استخدم الأزرار أدناه للتحكم الكامل في غرفتك الصوتية:",
            color=discord.Color.dark_embed()
        )
        embed.add_field(name="التحكم الأمني", value="🔒 Lock / 🔓 Unlock", inline=False)
        embed.add_field(name="التخصيص", value="✏️ Rename لتبديل الاسم", inline=False)
        embed.add_field(name="الدعم", value="🚨 Get Staff لطلب الإدارة العالية", inline=False)
        
        try:
            await new_vc.send(content=f"مرحباً بك {member.mention} في رومك الخاصة:", embed=embed, view=TempControlView(member.id))
        except Exception as e:
            print(f"خطأ في إرسال رسالة التحكم: {e}")

    # حذف الروم كي تخوى تماماً
    if before.channel and before.channel.id in active_temp_vcs and len(before.channel.members) == 0:
        try:
            await before.channel.delete()
            del active_temp_vcs[before.channel.id]
        except:
            pass

bot.run("")

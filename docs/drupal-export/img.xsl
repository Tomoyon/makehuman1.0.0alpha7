<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSL/Format">

  <xsl:template match="img">
    <xsl:text>

.. image:: </xsl:text><xsl:value-of select="@src" /><xsl:text>

</xsl:text>
  </xsl:template>

</xsl:stylesheet>

